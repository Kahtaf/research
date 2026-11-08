"""R3 boundaries, historical R2 quarantine, source preservation and provenance."""
import copy
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_transport as t

p, b, o = t.p, t.b, t.o
ROOT = p.ROOT
OLD = p.WORKSPACE / '2026-11-06-asus-linux49-probe-transport'
OLD_IMAGE_SHA = '48bb6efa1620cb380037e53b53cfa560e38cd23b95211c8634616ce94fd6ce48'


class R3Tests(unittest.TestCase):
    def test_original_r2_install_quarantine_with_every_attestation(self):
        old = t.load('historical_r2_transport', OLD / 'source/probe_transport.py')
        # No fake transport is supplied: the runner audit guard forbids process creation.
        local = old.verify_local()[2]
        with patch('sys.stdout', new_callable=io.StringIO), patch('sys.stderr', new_callable=io.StringIO) as error:
            code = old.main(['install', '--execute', '--run-id', t.RUN,
                             '--parent-reviewed', '--supervised', '--physical-fallback-present',
                             '--reviewed-profile-sha256', old.PROFILE_SHA,
                             '--reviewed-code-sha256', local['code']['sha256']])
        self.assertEqual(code, 2)
        self.assertIn('R2 INSTALL QUARANTINED', error.getvalue())
        receipt = json.loads((OLD / 'evidence/code-receipt.json').read_text())
        self.assertNotEqual(receipt['sha256'], local['code']['sha256'])

    def test_r2_image_has_no_r3_transport_or_observer_path(self):
        old = json.loads((OLD / 'profile.json').read_text())
        image = Path(old['candidate']['path'])
        self.assertEqual(b.sha(image.read_bytes()), OLD_IMAGE_SHA)
        with self.assertRaises(o.Refused):
            o.verify_image(image)
        with patch.object(o, 'IMAGE', image), self.assertRaises(b.Refused):
            p.verify_local()

    def test_real_product_r3_kernel_cannot_replace_combined_r1(self):
        product = p.KERNEL.with_name('Image.gz-dtb-combined-product-r3')
        self.assertTrue(product.is_file())
        self.assertNotEqual(b.sha(product.read_bytes()), p.KERNEL_SHA)
        with patch.object(p, 'KERNEL', product), self.assertRaisesRegex(b.Refused, 'Exact combined-r1'):
            p.verify_local()

    def test_r2_pin_rejected_by_new_observer(self):
        old = json.loads((OLD / 'profile.json').read_text())
        pin = t.pin(profile=old['profile'], candidate_sha256=old['candidate']['sha256'],
                    padded_sha256=old['candidate']['padded_sha256'])
        with self.assertRaises(b.Refused):
            p.validate_pin(pin, t.RUN)

    def test_only_corrected_initrd_token_passes(self):
        for token in ('0x44000200,0x11f7b0', '0x44000000,0x11f9b0', '0x44000000,0x200000',
                      '0x44000000,0x11f7b0 initrd=0x44000200,0x11f7b0',
                      '0x44000000,0x11f7b0 initrd=0x44000000,0x11f7b0'):
            report = t.observer_tests.report({'/proc/cmdline': 'androidboot.serialno=' + o.STOCK + ' initrd=' + token})
            result = o.validate_report(report, 0)
            self.assertTrue(result['report_collected'])
            self.assertFalse(result['diagnostic_requirements_passed'], token)
            self.assertFalse(result['hardware_ready'])
        self.assertTrue(o.validate_report(t.observer_tests.report(), 0)['diagnostic_requirements_passed'])

    def test_profile_is_precisely_derived_from_original_and_manifest(self):
        old = json.loads((OLD / 'profile.json').read_text())
        new = json.loads(p.PROFILE_FILE.read_text())
        manifest = json.loads((ROOT / 'evidence/reference/manifest.json').read_text())
        self.assertEqual(new['candidate']['sha256'], manifest['image_sha256'])
        self.assertEqual(new['candidate']['padded_sha256'], manifest['padded_partition_sha256'])
        self.assertEqual(new['candidate']['header_page_sha256'], manifest['header_page_sha256'])
        self.assertEqual(new['kernel']['packaged_dtb_sha256'], manifest['packaged_dtb_sha256'])
        self.assertEqual(new['ramdisk']['exact_entries'], old['ramdisk']['exact_entries'])
        self.assertEqual(new['control'], old['control'])
        self.assertEqual(new['target'], old['target'])
        self.assertEqual(new['ramdisk']['compressed_start'], '0x44000000')
        self.assertEqual(new['ramdisk']['compressed_end'], '0x4411f7b0')
        self.assertEqual(new['kernel']['input_sha256'], p.KERNEL_SHA)
        self.assertFalse(new['physical_execution_authorized'])
        self.assertFalse(new['provenance']['physical_boot_proven'])

    def test_header_and_dt_whole_image_pins_reject_corruption(self):
        image = o.IMAGE.read_bytes()
        self.assertEqual(b.sha(image[:2048]), '4b58f4a3032eb2814c54bafbe0c95337822dbdf0d940ff822ea8540e8e1687d8')
        self.assertEqual(len(image[64:576].split(b'\0')[0]), 95)
        self.assertEqual(struct.unpack_from('<I', image, 20)[0], 0x44000000)
        with tempfile.TemporaryDirectory(dir=ROOT / 'tests') as tmp:
            path = Path(tmp) / 'mutated.img'
            for offset in (64, 2048 + 512, 2048 + 512 + 7632565, len(image)-2048):
                changed = bytearray(image); changed[offset] ^= 1
                path.write_bytes(changed)
                with self.subTest(offset=offset), self.assertRaises(o.Refused):
                    o.verify_image(path)

    def test_reproduction_and_cpio_receipt(self):
        receipt = json.loads((ROOT / 'evidence/reproduction/receipt.json').read_text())
        self.assertEqual(receipt['status'], 'BYTE_IDENTICAL_METADATA_REPRODUCTION')
        self.assertEqual(receipt['image_sha256'], o.IMAGE_SHA)
        self.assertEqual(receipt['cpio_entries_verified'], 22)
        self.assertTrue(receipt['manifest_byte_identical'])
        self.assertFalse(receipt['physical_boot_proven'])

    def test_historical_sources_and_artifacts_unchanged(self):
        records = json.loads((ROOT / 'evidence/input-receipts.json').read_text())
        for name, receipt in records.items():
            with self.subTest(name=name):
                self.assertEqual(b.sha((p.WORKSPACE / name).read_bytes()), receipt['sha256'])

    def test_engine_only_staging_path_changed_and_shared_lock_retained(self):
        original = (OLD / 'source/recovery_control.py').read_text()
        expected = original.replace("BASE = '/data/local/tmp/asus-linux49-probe-transport'",
                                    "BASE = '/data/local/tmp/asus-linux49-r3-transport'")
        self.assertEqual((ROOT / 'source/recovery_control.py').read_text(), expected)
        old = t.load('historical_engine', OLD / 'source/recovery_control.py')
        self.assertEqual(b.EXECUTE_LOCK, old.EXECUTE_LOCK)
        self.assertEqual(b.DEVICE_GUARD, old.DEVICE_GUARD)
        self.assertNotEqual(b.BASE, old.BASE)
        self.assertEqual(t.legacy.c, b)
        self.assertEqual(t.observer_tests.o, o)

    def test_r3_observer_cannot_finalize_from_arbitrary_backup_cli(self):
        with patch('sys.argv', ['observer.py', 'finalize', '--execute']), self.assertRaisesRegex(o.Refused, 'actual restore/readback journal'):
            o.main()

    def test_r3_source_and_profile_pins_match_actual_copies(self):
        for path, expected in ((p.PROFILE_FILE, p.PROFILE_SHA), (p.OBSERVER_PATH, p.OBSERVER_SHA),
                               (ROOT / 'source/recovery_control.py', p.BASE_SHA)):
            self.assertEqual(b.sha(path.read_bytes()), expected)
        with tempfile.TemporaryDirectory(dir=ROOT / 'tests') as tmp:
            changed = Path(tmp) / 'changed.py'; changed.write_text('raise RuntimeError("must never execute")')
            with self.assertRaisesRegex(RuntimeError, 'Pinned source changed'):
                p.load_pinned('must_not_load', changed, p.OBSERVER_SHA)

    def test_prior_failure_evidence_still_present_and_not_relabelled(self):
        failed = json.loads((OLD / 'evidence/parent-replay-20261106T1840/failed-original-summary.json').read_text())
        self.assertEqual((failed['tests_run'], failed['failures'], failed['errors']), (32, 15, 1))
        self.assertEqual(failed['actual_subprocess_calls'], 0)
        replay = (OLD / 'evidence/parent-replay-20261106T1840/replay.txt').read_text()
        self.assertIn('Ran 32 tests', replay)
        self.assertIn('OK', replay)
