// SPDX-License-Identifier: Apache-2.0
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
  std::cout << "P00A_GENERATED_CONFIG_BEGIN\n" << writer.ToString()
            << "P00A_GENERATED_CONFIG_END\n";
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
