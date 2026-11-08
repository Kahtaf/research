"""Small filesystem/process behavior fixtures. Never use the production plan."""
import contextlib
import ctypes
import datetime
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import integrate as i
import verify_full_images as v
from validate_completed_product import materialize, verify_source_images
from verify_root_payload import verify as verify_root, verify_ramdisk_properties
from verify_input_payload import verify as verify_input, INSTALLED
sys.path.insert(0, str(ROOT / 'tests/packager/scripts'))
sys.path.insert(0, str(ROOT / 'tests/packager/probe'))
import package_full_boot as packager
from bootformat import make_cpio, pad, boot_id
from lk_contract import REQUIRED_INPUT


def put(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.encode() if isinstance(value, str) else value)
    return path

def jsonput(path, value): return put(path, json.dumps(value))


class OutputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='TEST_ONLY-', dir=ROOT / 'tests')
        self.root = Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()

    def input_tree(self, path):
        source = ROOT / 'inputs/input-files/input'
        for rel in INSTALLED:
            put(path / rel, (source / Path(rel).name).read_bytes())
        return path

    def test_installed_input_mapping_requires_exact_real_files(self):
        product = self.input_tree(self.root / 'product')
        self.assertEqual(len(verify_input(product)['checked']), 2)
        rel = next(iter(INSTALLED))
        path = product / rel
        original = path.read_bytes()
        path.write_bytes(b'touch.orientationAware=0\n')
        with self.assertRaisesRegex(i.Refusal, 'bytes differ'): verify_input(product)
        path.unlink()
        source = put(self.root / 'outside', original)
        path.symlink_to(source)
        with self.assertRaisesRegex(i.Refusal, 'missing or invalid'): verify_input(product)

    def test_real_ext4_input_mapping_bytes_and_system_root_layout(self):
        mkfs, debugfs = shutil.which('mkfs.ext4'), shutil.which('debugfs')
        if not mkfs or not debugfs: self.skipTest('actual e2fsprogs fixture requires Linux tools')
        product = self.input_tree(self.root / 'product')
        image = self.root / 'system.raw'
        with image.open('wb') as f: f.truncate(16 * 1024 * 1024)
        subprocess.run([mkfs, '-q', '-F', '-d', str(product), str(image)], check=True, capture_output=True)
        self.assertTrue(all(x['final_ext4_verified'] for x in verify_input(product, image, debugfs)['checked']))
        rel = 'system/vendor/usr/keylayout/mtk-kpd.kl'
        subprocess.run([debugfs, '-w', '-R', 'rm /' + rel, str(image)], check=True, capture_output=True)
        with self.assertRaisesRegex(i.Refusal, 'SYSTEM input mapping bytes differ'): verify_input(product, image, debugfs)
        bad = put(self.root / 'bad-map', 'key 116 VOLUME_DOWN\n')
        subprocess.run([debugfs, '-w', '-R', 'write ' + str(bad) + ' /' + rel, str(image)], check=True, capture_output=True)
        with self.assertRaisesRegex(i.Refusal, 'SYSTEM input mapping bytes differ'): verify_input(product, image, debugfs)
        flat = self.root / 'flat.raw'
        with flat.open('wb') as f: f.truncate(16 * 1024 * 1024)
        subprocess.run([mkfs, '-q', '-F', '-d', str(product / 'system'), str(flat)], check=True, capture_output=True)
        with self.assertRaisesRegex(i.Refusal, 'SYSTEM input mapping bytes differ'): verify_input(product, flat, debugfs)

    def vars_fixture(self):
        s = (ROOT / 'inputs/observed-r5.vars').read_text()
        # Only a text fixture for variable validation; never an actual product target.
        additional = 'p00a-wmt libbtcal libbt-vendor-p00a libbluetooth_mtk_p00a android.hardware.bluetooth@1.1-service.p00a wpa_supplicant P00aWifiBringupOverlay sensors.mt8163 android.hardware.sensors@1.0-service:64 android.hardware.sensors@1.0-impl:64 bpfloader vold'
        lines = [line[:-1] + ' ' + additional + "'" if line.startswith('PRODUCT_PACKAGES=') else line for line in s.splitlines()]
        return '\n'.join(lines) + '\n'

    def test_adb_root_and_adbd_required_secure_userdebug(self):
        path = put(self.root / 'vars', self.vars_fixture())
        v.variables(path)
        for token in ['adb_root', 'com.android.adbd']:
            path.write_text(self.vars_fixture().replace(' ' + token + ' ', ' '))
            with self.assertRaisesRegex(ValueError, 'missing required'): v.variables(path)
        path.write_text(self.vars_fixture().replace('ro.adb.secure=1', 'ro.adb.secure=0'))
        with self.assertRaisesRegex(ValueError, 'authenticated ADB'): v.variables(path)

    def test_real_output_root_route_requires_elf_rc_apex_and_secure_props(self):
        product = self.root / 'product'
        apex = self.root / 'apex'
        elf = bytearray(64)
        elf[:6] = b'\x7fELF\x02\x01'
        struct.pack_into('<H', elf, 18, 183)
        put(product / 'system/system_ext/bin/adb_root', bytes(elf))
        rc = put(product / 'system/system_ext/etc/init/adb_root.rc', 'TEST_ONLY root init')
        put(product / 'system/apex/com.android.adbd.apex', 'TEST_ONLY source APEX')
        put(apex / 'com.android.adbd/bin/adbd', bytes(elf))
        metadata = put(apex / 'apex-info-list.xml', '<apex-info-list><apex-info moduleName="com.android.adbd" isActive="true" modulePath="/system/apex/com.android.adbd.apex"/></apex-info-list>')
        props = put(product / 'system/build.prop', 'ro.secure=1\nro.debuggable=1\nro.adb.secure=1\n')
        result = verify_root(product, apex, i.sha(rc))
        self.assertFalse(result['root_runtime_verified'])
        props.write_text('ro.secure=0\nro.debuggable=1\nro.adb.secure=1\n')
        with self.assertRaisesRegex(i.Refusal, 'property mismatch'): verify_root(product, apex, i.sha(rc))
        props.write_text('ro.secure=1\nro.debuggable=1\nro.adb.secure=1\n')
        metadata.write_text('<apex-info-list/>')
        with self.assertRaisesRegex(i.Refusal, 'exactly one adbd'): verify_root(product, apex, i.sha(rc))
        with self.assertRaisesRegex(i.Refusal, 'Insecure actual ramdisk'):
            verify_ramdisk_properties({'prop.default': (0o100644, 0, 0, b'ro.adb.secure=0\n')}, product)

    def test_zero_ranges_and_partition_tail_are_written(self):
        source = self.root / 'sparse-input'
        with source.open('wb') as f:
            f.write(b'A')
            f.seek(1024 * 1024)
            f.write(b'Z')
        out = self.root / 'raw'
        materialize(source, out, 2 * 1024 * 1024)
        self.assertEqual(out.read_bytes(), b'A' + bytes(1024 * 1024 - 1) + b'Z' + bytes(1024 * 1024 - 1))
        # Linux fixture filesystem accounting is evidence that zero writes weren't seeks.
        if sys.platform == 'linux': self.assertGreaterEqual(out.stat().st_blocks * 512, out.stat().st_size)

    def test_source_image_changes_refused(self):
        put(self.root / 'boot.img', 'actual source')
        put(self.root / 'system.img', 'actual system')
        report = {n: {'sha256': i.sha(self.root / (n + '.img'))} for n in ('boot', 'system')}
        verify_source_images(self.root, report)
        put(self.root / 'boot.img', 'mutated')
        with self.assertRaisesRegex(i.Refusal, 'Source image changed'): verify_source_images(self.root, report)

    def test_wrong_full_boot_hash_kernel_and_synthetic_rejected(self):
        kernel = b'TEST_ONLY_not_a_kernel'
        ram = gzip.compress(make_cpio({'NONBOOTABLE-SYNTHETIC-FIXTURE.txt': (0o100644, 0, 0, b'TEST ONLY')}), mtime=0)
        header = bytearray(2048)
        header[:8] = b'ANDROID!'
        struct.pack_into('<10I', header, 8, len(kernel), 0x40080000, len(ram), 0x44000000, 0, 0x40f00000, 0x4e000000, 2048, 0, 0)
        command = b' '.join(k + b'=' + x for k, x in REQUIRED_INPUT.items())
        header[64:64+len(command)] = command
        header[576:608] = boot_id(kernel, ram)
        data = bytes(header) + pad(kernel) + pad(ram)
        with self.assertRaisesRegex(ValueError, 'report hash mismatch'): packager.package(data, kernel, {'boot': {'sha256': '0' * 64}})
        report = {'boot': {'sha256': hashlib.sha256(data).hexdigest()}}
        with self.assertRaisesRegex(ValueError, 'Kernel differs'): packager.package(data, b'wrong', report)
        with self.assertRaisesRegex(ValueError, 'Synthetic fixture rejected'): packager.package(data, kernel, report)
        empty = gzip.compress(make_cpio({'file': (0o100644, 0, 0, b'no init')}), mtime=0)
        with self.assertRaisesRegex(ValueError, 'Missing first-stage init'): packager.validate_ramdisk(empty, False)

    def test_no_clean_or_unbounded_compile_command_in_build(self):
        script = (ROOT / 'scripts/build.sh').read_text()
        commands = [l.strip() for l in script.splitlines() if l.strip().startswith('m ')]
        self.assertEqual(len(commands), 2)
        self.assertTrue(all(c.startswith('m -j8 ') for c in commands))
        self.assertFalse(any('installclean' in c or ' clean' in c for c in commands))
        self.assertIn('sepolicy_neverallows', commands[0])
        self.assertIn('adb_root com.android.adbd', commands[0])
        self.assertEqual(commands[-1], 'm -j8 bootimage systemimage')
        self.assertNotIn('/srv/android/asus-build-continuation/scripts/', script)
        self.assertNotIn('SYNTHETIC_FIXTURE', script)

if __name__ == '__main__': unittest.main(verbosity=2)
