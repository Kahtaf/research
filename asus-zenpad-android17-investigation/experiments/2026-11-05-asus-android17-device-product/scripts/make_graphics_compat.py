#!/usr/bin/env python3
"""Generate the narrow linkerconfig patch against saved pre-r5 source."""
from pathlib import Path
import argparse
import difflib
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
BEFORE = ROOT / 'evidence/graphics-astra/linkerconfig-before'
parser = argparse.ArgumentParser()
parser.add_argument('--revision', required=True)
args = parser.parse_args()
assert args.revision.isalnum()
OUT = ROOT / ('compatibility/graphics-' + args.revision)
assert not OUT.exists(), 'Preserve generated revisions'
OUT.mkdir(exist_ok=True)
files = {str(p.relative_to(BEFORE)): p.read_text() for p in BEFORE.rglob('*') if p.is_file()}
after = dict(files)
def replace(path, old, new):
    assert after[path].count(old) == 1, (path, old)
    after[path] = after[path].replace(old, new)
replace('Android.bp', '    name: "linkerconfig_defaults",\n', '''    name: "linkerconfig_defaults",
    cflags: select(soong_config_variable("p00a", "legacy_graphics"), {
        true: ["-DP00A_LEGACY_GRAPHICS"],
        default: [],
    }) + [
        "-Wall",
        "-Werror",
        "-Wextra",
    ],
''')
# Replace the original cflags list only, leaving the newly inserted one intact.
replace('Android.bp', '    ],\n    cflags: [\n        "-Wall",\n        "-Werror",\n        "-Wextra",\n    ],\n    defaults:', '    ],\n    defaults:')
replace('modules/include/linkerconfig/environment.h', 'bool IsVndkLiteDevice();', 'bool IsP00aLegacyGraphics();\nbool IsVndkLiteDevice();')
replace('modules/environment.cc', '#include <unistd.h>', '#include <unistd.h>\n#include <android-base/parseint.h>')
replace('modules/environment.cc', 'bool IsVndkLiteDevice() {', '''bool IsP00aLegacyGraphics() {
#ifdef P00A_LEGACY_GRAPHICS
  unsigned int first_api = 0;
  return android::base::ParseUint(
             Variables::GetValue("ro.product.first_api_level").value_or(""),
             &first_api) &&
         first_api > 0 && first_api < 26 &&
         !IsVendorVndkVersionDefined() && !IsProductVndkVersionDefined();
#else
  return false;
#endif
}

bool IsVndkLiteDevice() {''')
replace('contents/namespace/systemdefault.cc', '  SetupSystemPermittedPaths(&ns);', '''  SetupSystemPermittedPaths(&ns);

  if (ctx.IsDefaultConfig() && modules::IsP00aLegacyGraphics()) {
    // Pre-Treble graphics use one core ABI. Core paths stay first, with vendor
    // paths retained for the current HIDL passthrough adapters and EGL alias.
    ns.AddSearchPath("/vendor/${LIB}");
    ns.AddSearchPath("/vendor/${LIB}/hw");
    ns.AddPermittedPath("/system/${LIB}/egl");
    ns.AddPermittedPath("/vendor/${LIB}");
    ns.AddPermittedPath("/system/vendor/${LIB}");
  }''')
replace('contents/namespace/sphal.cc', '  // Visible to allow use with android_dlopen_ext, and with', '''  if (ctx.IsDefaultConfig() &&
      (ctx.IsSystemSection() || ctx.IsUnrestrictedSection()) &&
      modules::IsP00aLegacyGraphics()) {
    // Forward HAL loads to the core namespace, sharing Binder and C++ state.
    // Keep this namespace isolated, visible, and without its own search paths.
    Namespace ns("sphal", /*is_isolated=*/true, /*is_visible=*/true);
    ns.GetLink(ctx.GetSystemNamespaceName()).AllowAllSharedLibs();
    return ns;
  }

  // Visible to allow use with android_dlopen_ext, and with''')
replace('contents/namespace/vendordefault.cc', '  return BuildVendorNamespace(ctx, "default");', '''  if (ctx.IsDefaultConfig() && modules::IsP00aLegacyGraphics()) {
    // The legacy product has no VNDK contract. Vendor services must use the
    // same core Binder/libutils ABI as its system-installed gralloc closure.
    return BuildSystemDefaultNamespace(ctx);
  }
  return BuildVendorNamespace(ctx, "default");''')
after['contents/tests/configuration/p00a_legacy_graphics_test.cc'] = '''// SPDX-License-Identifier: Apache-2.0
#include <algorithm>
#include <iostream>

#include <gtest/gtest.h>
#include "linkerconfig/apex.h"
#include "mockenv.h"
#include "linkerconfig/baseconfig.h"
#include "linkerconfig/configwriter.h"
#include "linkerconfig/environment.h"
#include "linkerconfig/namespacebuilder.h"

using namespace android::linkerconfig::contents;
using namespace android::linkerconfig::modules;

class P00aLegacyGraphics : public ::testing::Test {
 protected:
  void SetUp() override {
    MockGenericVariables();
    Variables::AddValue("ro.product.first_api_level", "23");
    Variables::AddValue("ro.vndk.version", "");
    Variables::AddValue("ro.product.vndk.version", "");
  }
  void TearDown() override {
    Variables::AddValue("ro.product.first_api_level", "");
    MockGenericVariables();
  }
};

TEST_F(P00aLegacyGraphics, RejectsMissingMalformedAndModernApi) {
  for (const auto* api : {"", "0", "-1", "garbage", "26", "37"}) {
    Variables::AddValue("ro.product.first_api_level", api);
    EXPECT_FALSE(IsP00aLegacyGraphics()) << api;
    Context ctx;
    auto ns = BuildSystemDefaultNamespace(ctx);
    EXPECT_EQ(ns.SearchPaths().size(), 2u);
    auto sphal = BuildSphalNamespace(ctx);
    EXPECT_FALSE(sphal.SearchPaths().empty());
  }
}

TEST_F(P00aLegacyGraphics, RejectsVndkProducts) {
  Variables::AddValue("ro.vndk.version", "29");
  EXPECT_FALSE(IsP00aLegacyGraphics());
  Variables::AddValue("ro.vndk.version", "");
  Variables::AddValue("ro.product.vndk.version", "29");
  EXPECT_FALSE(IsP00aLegacyGraphics());
}

#ifdef P00A_LEGACY_GRAPHICS
TEST_F(P00aLegacyGraphics, CoreAbiIsSharedAndNamespacesStayIsolated) {
  ASSERT_TRUE(IsP00aLegacyGraphics());
  Context ctx;
  auto system = BuildSystemDefaultNamespace(ctx);
  ASSERT_EQ(system.SearchPaths().size(), 4u);
  EXPECT_EQ(system.SearchPaths().front(), "/system/${LIB}");
  ConfigWriter system_writer;
  system.WriteConfig(system_writer);
  EXPECT_NE(system_writer.ToString().find("namespace.default.isolated = true"), std::string::npos);
  auto sphal = BuildSphalNamespace(ctx);
  EXPECT_TRUE(sphal.IsVisible());
  EXPECT_TRUE(sphal.SearchPaths().empty());
  ASSERT_EQ(sphal.Links().size(), 1u);
  EXPECT_EQ(sphal.Links().front().To(), "default");
  EXPECT_TRUE(sphal.Links().front().IsAllSharedLibsAllowed());
  ctx.SetCurrentSection(SectionType::Vendor);
  auto vendor = BuildVendorDefaultNamespace(ctx);
  EXPECT_EQ(vendor.SearchPaths(), system.SearchPaths());
  auto config = CreateBaseConfiguration(ctx);
  ConfigWriter writer;
  config.WriteConfig(writer);
  std::cout << "P00A_GENERATED_CONFIG_BEGIN\\n" << writer.ToString()
            << "P00A_GENERATED_CONFIG_END\\n";
}

TEST_F(P00aLegacyGraphics, DoesNotChangeApexOrRecoveryNamespaces) {
  Context ctx;
  for (auto type : {LinkerConfigType::ApexBinary, LinkerConfigType::Recovery}) {
    ctx.SetCurrentLinkerConfigType(type);
    auto system = BuildSystemDefaultNamespace(ctx);
    EXPECT_EQ(system.SearchPaths().size(), 2u);
    auto vendor = BuildVendorDefaultNamespace(ctx);
    EXPECT_EQ(vendor.SearchPaths().front(), "/odm/${LIB}");
  }
}
#else
TEST_F(P00aLegacyGraphics, NoCompatibilityWithoutProductOptIn) {
  EXPECT_FALSE(IsP00aLegacyGraphics());
}
#endif
'''
patch = ''.join(''.join(difflib.unified_diff(files.get(p, '').splitlines(True), text.splitlines(True),
               fromfile='a/'+p if p in files else '/dev/null', tofile='b/'+p))
               for p, text in after.items() if files.get(p) != text)
(OUT / 'linkerconfig.patch').write_text(patch)
(OUT / 'source-manifest.json').write_text(json.dumps({p: dict(
    before_sha256=hashlib.sha256(files[p].encode()).hexdigest() if p in files else None,
    after_sha256=hashlib.sha256(text.encode()).hexdigest()) for p,text in after.items()}, indent=2)+'\n')
print(f'Generated {len(patch)} byte patch for {len(after)} files')
