#!/usr/bin/env python3
"""Small failure/atomicity fixtures only; never extract the real payload."""

import copy
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import stage_inline as stager


class StagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=stager.ROOT / "evidence", prefix=".stager-test-")
        self.root = Path(self.temp.name)
        (self.root / "build/soong").mkdir(parents=True)
        (self.root / "vendor").mkdir()
        self.blobs = stager.read_tree()
        self.original = stager.metadata(self.blobs)
        self.adapted = stager.adapted_metadata(self.original)
        self.groups, self.excluded = stager.payload_groups(self.blobs)
        self.plan = stager.plan(self.blobs, self.original, self.adapted, self.groups, self.excluded)

    def tearDown(self):
        self.temp.cleanup()

    def tiny_fixture(self):
        member = "system/product/priv-app/Fixture/Fixture.apk"
        chunks = [b"first", b"second"]
        entries = [{"path": f"arm64/proprietary/product/priv-app/Fixture/Fixture.apk.{i:02d}",
                    "size": len(b), "sha": stager.git_blob(b), "mode": "100644"} for i, b in enumerate(chunks)]
        groups = {member: entries}
        p = self.root / "fixture.zip"
        with zipfile.ZipFile(p, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(member, b"".join(chunks))
            for name in sorted(stager.INSTALLER_MEMBERS | {"system/" + stager.TITAN} |
                               {f"system/product/overlay/{x}.apk" for x in stager.OVERLAYS}):
                z.writestr(name, b"fixture")
        plan = stager.plan(self.blobs, self.original, self.adapted, groups, self.excluded)
        return p, groups, plan

    def fixture_constants(self, p):
        return patch.multiple(stager, ZIP_SIZE=p.stat().st_size, ZIP_SHA256=stager.file_digest(p))

    def test_real_manifest_matches_pinned_inputs(self):
        proof = stager.read_verified_manifest(stager.ROOT / "evidence/inline-source-manifest.json", self.plan)
        self.assertEqual(proof["payload_bytes"], 734740442)
        self.assertEqual(len(proof["outputs"]), 64)

    def test_product_wrapper_works_before_boardconfig_defines_arch(self):
        wrapper = self.root / "google.mk"
        wrapper.write_bytes(self.adapted["asus-p00a-google.mk"])
        for product, grouper, success in (("lineage_p00a", "", True), ("other", "", False),
                                          ("lineage_p00a", "true", False)):
            text = (f"TARGET_PRODUCT := {product}\nTARGET_ARCH :=\nTARGET_IS_GROUPER := {grouper}\n"
                    "inherit-product = $(info inherit=$(strip $(1)))\n"
                    f"include {wrapper}\nall: ;\n")
            result = subprocess.run(["make", "-f", "-"], input=text, text=True, capture_output=True)
            self.assertEqual(result.returncode == 0, success, result.stderr)
            if success:
                self.assertIn("inherit=vendor/gapps/arm64/arm64-vendor.mk", result.stdout)

    def test_all_staged_blueprint_paths_and_module_references_exist(self):
        outputs = self.plan["outputs"]
        names = set()
        refs = set()
        for p, data in self.adapted.items():
            if not p.endswith("Android.bp"):
                continue
            text = data.decode()
            names.update(re.findall(r'\bname:\s*"([^"]+)"', text))
            refs.update(re.findall(r'":([^"]+)"', text))
            for path in re.findall(r'"(proprietary/[^"]+)"', text):
                self.assertIn(str(Path(p).parent / path), outputs)
        self.assertTrue(refs <= names)
        self.assertIn("PrebuiltGmsCoreVic", names)
        self.assertNotIn("VelvetTitan", names)
        self.assertEqual(self.adapted["dummy-apps/Android.bp"], self.original["dummy-apps/Android.bp"])
        for p in self.original:
            if p.startswith("overlay/"):
                self.assertEqual(self.adapted[p], self.original[p])

    def test_reject_modified_manifest_inventory(self):
        p = self.root / "proof.json"
        proof = json.loads((stager.ROOT / "evidence/inline-source-manifest.json").read_text())
        proof["outputs"].pop("dummy-apps/Android.bp")
        p.write_text(json.dumps(proof))
        with self.assertRaisesRegex(ValueError, "inventory"):
            stager.read_verified_manifest(p, self.plan)

    def test_split_reconstruction_and_disk_output(self):
        p, groups, plan = self.tiny_fixture()
        with self.fixture_constants(p):
            expected = stager.verify(p, copy.deepcopy(plan), groups)
            with patch.object(stager.sys, "platform", "linux"):
                stager.stage(self.root, p, expected, plan, self.adapted, self.blobs, groups)
            stager.check_stage(self.root / "vendor/gapps", expected)
            self.assertEqual((self.root / "vendor/gapps/arm64/proprietary/product/priv-app/Fixture/Fixture.apk.01").read_bytes(), b"second")
            with patch.object(stager.sys, "platform", "linux"):
                with self.assertRaisesRegex(ValueError, "already exists"):
                    stager.stage(self.root, p, expected, plan, self.adapted, self.blobs, groups)
            (self.root / "vendor/gapps/dummy-apps/Android.bp").write_bytes(b"corrupt")
            with self.assertRaisesRegex(ValueError, "staged bytes mismatch"):
                stager.check_stage(self.root / "vendor/gapps", expected)

    def test_failed_stage_cleans_its_private_directory(self):
        p, groups, plan = self.tiny_fixture()
        groups[next(iter(groups))][1]["sha"] = "0" * 40
        with self.fixture_constants(p), patch.object(stager.sys, "platform", "linux"):
            with self.assertRaisesRegex(ValueError, "Git blob mismatch"):
                stager.stage(self.root, p, {}, plan, self.adapted, self.blobs, groups)
        self.assertEqual(list((self.root / "vendor").iterdir()), [])

    def test_same_size_release_corruption_rejected(self):
        p, groups, plan = self.tiny_fixture()
        with self.fixture_constants(p):
            b = bytearray(p.read_bytes())
            b[len(b) // 2] ^= 1
            p.write_bytes(b)
            with self.assertRaisesRegex(ValueError, "release ZIP SHA256"):
                stager.verify(p, plan, groups)

    def test_zip_inventory_rejects_extra_and_duplicate_members(self):
        for unexpected in ("unexpected.apk", "../escape", "build.prop"):
            p, groups, plan = self.tiny_fixture()
            with zipfile.ZipFile(p, "a") as z:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    z.writestr(unexpected, b"bad")
            with zipfile.ZipFile(p) as z:
                with self.assertRaises(ValueError):
                    stager.zip_inventory(z, groups)

    def test_mac_full_payload_stage_is_refused(self):
        with patch.object(stager.sys, "platform", "darwin"):
            with self.assertRaisesRegex(ValueError, "Linux-builder-only"):
                stager.stage(self.root, self.root / "missing.zip", {}, self.plan, self.adapted, self.blobs, self.groups)
        self.assertEqual(list((self.root / "vendor").iterdir()), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
