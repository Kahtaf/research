import copy
import importlib.util
import json
import hashlib
import os
from pathlib import Path
import plistlib
import struct
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import stat
import unittest
from unittest import mock

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('observer', BASE / 'scripts/observe.py')
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)


def fixture_image(report=None):
    if report is None:
        report = ''.join(f'{k}={v}\n' for k, v in observer.CONTRACT['report_exact_fields'].items()).encode()
    raw = bytearray(65536)
    raw[:11] = b'\xeb\x3c\x90RAMPROBE'
    struct.pack_into('<HBHBHHBHHHII', raw, 11, 512, 1, 1, 2, 32, 128, 248, 1, 1, 1, 0, 0)
    raw[38] = 0x29
    struct.pack_into('<I', raw, 39, 0x617e2e06)
    raw[43:62] = b'RAMPROBE   FAT12   '
    raw[510:512] = b'\x55\xaa'
    raw[512:518] = b'\xf8\xff\xff\xff\x0f\x00'
    raw[1024:1536] = raw[512:1024]
    raw[1536:1548] = b'RAMPROBE   \x08'
    raw[1568:1580] = b'REPORT  TXT\x01'
    struct.pack_into('<H', raw, 1594, 2)
    struct.pack_into('<I', raw, 1596, len(report))
    raw[2560:2560+len(report)] = report
    return raw


def fixture_tree():
    return [{'IOObjectClass': 'IOUSBHostDevice', 'IORegistryEntryID': 101,
             'USB Serial Number': observer.SERIAL, 'IORegistryEntryChildren': [
                 {'IOObjectClass': 'IOUSBHostInterface', 'bInterfaceClass': 8,
                  'bInterfaceSubClass': 6, 'bInterfaceProtocol': 80, 'IORegistryEntryChildren': [
                      {'IOObjectClass': 'IOMedia', 'Whole': True, 'Size': 65536,
                       'Writable': False, 'BSD Name': 'disk12', 'IORegistryEntryID': 102}]}]}]


def fixture_disk():
    return {'DeviceIdentifier': 'disk12', 'DeviceNode': '/dev/disk12', 'Whole': True,
            'TotalSize': 65536, 'Writable': False, 'MountPoint': '/Volumes/RAMPROBE'}


class FatTests(unittest.TestCase):
    def test_exact_report_accepted(self):
        fields, report = observer.parse_fat(fixture_image())
        self.assertEqual(fields, observer.CONTRACT['report_exact_fields'])
        self.assertEqual(len(report.splitlines()), 7)

    def test_structural_mutations_refused(self):
        mutations = [(11, 1), (13, 2), (16, 1), (19, 127), (30, 1), (43, 88),
                     (54, 88), (510, 0), (1027, 0), (1536, 88), (1547, 0),
                     (1568, 88), (1579, 0), (1594, 3), (1600, 88), (4096, 1)]
        for offset, value in mutations:
            with self.subTest(offset=offset):
                raw = fixture_image()
                raw[offset] = value
                with self.assertRaises(observer.Refused):
                    observer.parse_fat(raw)

    def test_schema_mutations_refused(self):
        good = observer.parse_fat(fixture_image())[1]
        reports = [good.replace(b'pid1=1', b'pid1=0'), good.replace(b'sysname=Linux', b'sysname=Other'),
                   good.replace(b'release=3.18.35', b'release=3.18.36'),
                   good.replace(b'machine=aarch64', b'machine=armv7'),
                   good.replace(b'status=pid1_ram_report_ready', b'status=ready'),
                   good.replace(observer.SERIAL.encode(), b'0' * 36), good + b'extra=x\n',
                   good.replace(b'pid1=1\n', b''), good.replace(b'pid1=1\n', b'run_id=x\n'),
                   good.replace(b'\n', b'\r\n'), good[:-1], good.replace(b'Linux', b'\xffinux')]
        for report in reports:
            with self.subTest(report=report):
                with self.assertRaises(observer.Refused):
                    observer.parse_fat(fixture_image(report))

    def test_short_and_long_images_refused(self):
        for image in [fixture_image()[:-1], fixture_image() + b'\x00']:
            with self.assertRaises(observer.Refused):
                observer.parse_fat(image)


class IdentityTests(unittest.TestCase):
    def test_exact_scsi_readonly_media(self):
        identity = observer.select_media(fixture_tree())
        self.assertEqual(identity['disk'], 'disk12')
        self.assertEqual(observer.verify_disk(fixture_disk(), identity)['mount_point'], '/Volumes/RAMPROBE')

    def test_serial_missing_duplicate_or_wrong_class_refused(self):
        tree = fixture_tree()
        bad = [[], tree + copy.deepcopy(tree)]
        for key, value in [('USB Serial Number', 'old'), ('IOObjectClass', 'other'), ('IORegistryEntryID', None)]:
            changed = copy.deepcopy(tree)
            changed[0][key] = value
            bad.append(changed)
        for item in bad:
            with self.assertRaises(observer.Refused):
                observer.select_media(item)

    def test_other_interface_and_duplicate_interface_refused(self):
        tree = fixture_tree()
        tree[0]['IORegistryEntryChildren'][0]['bInterfaceClass'] = 255
        with self.assertRaises(observer.Refused):
            observer.select_media(tree)
        tree = fixture_tree()
        tree[0]['IORegistryEntryChildren'].append({'bInterfaceClass': 255})
        with self.assertRaises(observer.Refused):
            observer.select_media(tree)

    def test_uncertain_or_writable_media_refused(self):
        for key, value in [('Writable', True), ('Writable', None), ('Whole', False),
                           ('Size', 65535), ('BSD Name', 'disk1s1'), ('BSD Name', '../disk1'),
                           ('IORegistryEntryID', None)]:
            with self.subTest(key=key, value=value):
                tree = fixture_tree()
                tree[0]['IORegistryEntryChildren'][0]['IORegistryEntryChildren'][0][key] = value
                with self.assertRaises(observer.Refused):
                    observer.select_media(tree)

    def test_diskutil_identity_capacity_and_write_contradictions_refused(self):
        identity = observer.select_media(fixture_tree())
        for key, value in [('DeviceIdentifier', 'disk1'), ('DeviceNode', '/dev/disk1'), ('Whole', False),
                           ('TotalSize', 100000), ('Writable', True), ('MediaReadOnly', False),
                           ('ReadOnlyMedia', False)]:
            with self.subTest(key=key):
                info = fixture_disk()
                info[key] = value
                with self.assertRaises(observer.Refused):
                    observer.verify_disk(info, identity)


class ControlFlowTests(unittest.TestCase):
    def setUp(self):
        patch = mock.patch('builtins.print')
        patch.start()
        self.addCleanup(patch.stop)

    def test_default_does_not_call_host_commands(self):
        with mock.patch.object(sys, 'argv', ['observe.py']), mock.patch.object(subprocess, 'run') as run:
            self.assertEqual(observer.main(), 0)
            run.assert_not_called()

    def test_stale_baseline_prevents_disk_command_or_raw_read(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'trial'
            with mock.patch.object(sys, 'platform', 'darwin'), \
                 mock.patch.object(observer, 'snapshot', return_value=fixture_tree()), \
                 mock.patch.object(observer, 'command') as command:
                self.assertEqual(observer.observe(output, 1), 2)
                command.assert_not_called()

    def test_fixture_trial_reads_only_after_identity_and_rechecks(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'trial'
            with mock.patch.object(sys, 'platform', 'darwin'), \
                 mock.patch.object(observer, 'snapshot', side_effect=[[], fixture_tree(), fixture_tree(), fixture_tree()]), \
                 mock.patch.object(observer, 'command', side_effect=[plistlib.dumps(fixture_disk()),
                                     bytes(fixture_image()), plistlib.dumps(fixture_disk())]) as command:
                self.assertEqual(observer.observe(output, 1), 0)
                self.assertEqual(command.call_args_list[1].args[0][-1], '/dev/rdisk12')
                self.assertEqual((output / 'media.raw').stat().st_size, 65536)

    def test_read_identity_change_never_reports_positive(self):
        changed = fixture_tree()
        changed[0]['IORegistryEntryID'] = 999
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(sys, 'platform', 'darwin'), \
                 mock.patch.object(observer, 'snapshot', side_effect=[[], fixture_tree(), fixture_tree(), changed]), \
                 mock.patch.object(observer, 'command', side_effect=[plistlib.dumps(fixture_disk()), bytes(fixture_image())]):
                self.assertEqual(observer.observe(Path(directory) / 'trial', 1), 2)


class ReceiptTests(unittest.TestCase):
    def make_receipt(self, directory, changes=None):
        path = Path(directory) / 'baseline-receipt.json'
        snapshot = plistlib.dumps([])
        (path.parent / 'baseline-ioreg.plist').write_bytes(snapshot)
        receipt = {'kind': 'ABSENT_SERIAL_BASELINE_ONLY', 'serial': observer.SERIAL,
                   'snapshot': 'baseline-ioreg.plist',
                   'snapshot_sha256': hashlib.sha256(snapshot).hexdigest(),
                   'host_boot_fingerprint': 'fixture-boot', 'created_monotonic': time.monotonic(),
                   'expires_after_seconds': 180}
        receipt.update(changes or {})
        path.write_text(json.dumps(receipt))
        path.chmod(0o600)
        return path

    def test_receipt_is_consumed_once_and_baseline_copied(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_receipt(directory)
            output = Path(directory) / 'trial'
            output.mkdir()
            with mock.patch.object(observer, 'host_boot_fingerprint', return_value='fixture-boot'):
                result = observer.consume_baseline(path, output, time.monotonic() + 1)
                self.assertLess(result['age_seconds'], 180)
                self.assertTrue((output / 'baseline-ioreg.plist').exists())
                self.assertFalse(path.exists())
                with self.assertRaises(observer.Refused):
                    observer.consume_baseline(path, output, time.monotonic() + 1)

    def test_expired_wrong_boot_hash_timestamp_and_serial_refused(self):
        changes = [{'created_monotonic': time.monotonic() - 181}, {'host_boot_fingerprint': 'other'},
                   {'snapshot_sha256': 'wrong'}, {'created_monotonic': 'bad'}, {'serial': 'other'}]
        for change in changes:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                path = self.make_receipt(directory, change)
                output = Path(directory) / 'trial'
                output.mkdir()
                with mock.patch.object(observer, 'host_boot_fingerprint', return_value='fixture-boot'):
                    with self.assertRaises(observer.Refused):
                        observer.consume_baseline(path, output, time.monotonic() + 1)

    def test_unowned_mode_and_symlink_refused_before_consumption(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_receipt(directory)
            path.chmod(0o644)
            with self.assertRaises(observer.Refused):
                observer.consume_baseline(path, Path(directory), time.monotonic() + 1)
            self.assertTrue(path.exists())
            path.chmod(0o600)
            target = path.with_name('real.json')
            path.rename(target)
            path.symlink_to(target)
            with self.assertRaises(observer.Refused):
                observer.consume_baseline(path, Path(directory), time.monotonic() + 1)

    def test_observe_can_collect_already_enumerated_device_with_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = self.make_receipt(directory)
            with mock.patch.object(sys, 'platform', 'darwin'), \
                 mock.patch('builtins.print'), \
                 mock.patch.object(observer, 'host_boot_fingerprint', return_value='fixture-boot'), \
                 mock.patch.object(observer, 'snapshot', side_effect=[fixture_tree(), fixture_tree(), fixture_tree()]), \
                 mock.patch.object(observer, 'command', side_effect=[plistlib.dumps(fixture_disk()), bytes(fixture_image()),
                                    plistlib.dumps(fixture_disk())]):
                self.assertEqual(observer.observe(Path(directory) / 'trial', 1, receipt), 0)

    def test_baseline_live_host_calls_are_mocked(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'baseline'
            def snapshot(folder, name, deadline):
                (folder / (name + '.plist')).write_bytes(plistlib.dumps([]))
                return []
            with mock.patch.object(sys, 'platform', 'darwin'), mock.patch('builtins.print'), \
                 mock.patch.object(observer, 'snapshot', side_effect=snapshot), \
                 mock.patch.object(observer, 'host_boot_fingerprint', return_value='fixture-boot'):
                self.assertEqual(observer.baseline_only(output), 0)
                self.assertEqual(os.stat(output / 'baseline-receipt.json').st_mode & 0o777, 0o600)


class VolumeTests(unittest.TestCase):
    def mounted_info(self):
        info = fixture_disk()
        info.update(VolumeName='RAMPROBE', ReadOnlyVolume=True)
        return info

    def reader_details(self):
        report = observer.parse_fat(fixture_image())[1].decode()
        return {'report_text': report, 'mountpoint': '/Volumes/RAMPROBE', 'filesystem_readonly': True,
                'root_st_dev': 22, 'report_st_dev': 22, 'report_st_ino': 99,
                'report_size': len(report), 'filesystem_flags': os.ST_RDONLY}

    def test_explicit_mounted_volume_success_has_no_raw_fat_or_media_hash(self):
        info = self.mounted_info()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'trial'
            with mock.patch.object(sys, 'platform', 'darwin'), mock.patch('builtins.print'), \
                 mock.patch.object(observer, 'snapshot', side_effect=[[], fixture_tree(), fixture_tree(), fixture_tree(), fixture_tree()]), \
                 mock.patch.object(observer, 'command', side_effect=[plistlib.dumps(info), plistlib.dumps(info),
                     json.dumps(self.reader_details()).encode(), plistlib.dumps(info)]) as command:
                self.assertEqual(observer.observe(output, 1, report_via_volume=True), 0)
                result = json.loads((output / 'result.json').read_text())
                self.assertEqual(result['status'], 'POSITIVE_PID1_REPORT_VIA_READONLY_VOLUME')
                self.assertFalse(result['raw_FAT_verified'])
                self.assertNotIn('media_sha256', result)
                self.assertFalse((output / 'media.raw').exists())
                self.assertFalse(any('mount' in call.args[0] for call in command.call_args_list))

    def test_only_exact_identified_disk_is_mounted_readonly_when_needed(self):
        before = self.mounted_info()
        before.pop('MountPoint')
        info = self.mounted_info()
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(observer, 'snapshot', return_value=fixture_tree()), \
                 mock.patch.object(observer, 'command', side_effect=[b'mounted', plistlib.dumps(info),
                     json.dumps(self.reader_details()).encode()]) as command:
                observer.collect_volume_report(Path(directory), before, observer.select_media(fixture_tree()),
                    ['/usr/sbin/diskutil', 'info', '-plist', '/dev/disk12'], time.monotonic() + 1)
                self.assertEqual(command.call_args_list[0].args[0],
                                 ['/usr/sbin/diskutil', 'mount', 'readOnly', '/dev/disk12'])
                self.assertEqual(command.call_args_list[0].kwargs['record_path'], Path(directory) / 'mount-command.json')

    def test_bad_mountpoints_and_volume_write_flags_refused(self):
        identity = observer.select_media(fixture_tree())
        for change in [{'MountPoint': '/tmp/RAMPROBE'}, {'MountPoint': '/Volumes/../tmp'},
                       {'MountPoint': '/Volumes//RAMPROBE'}, {'MountPoint': None}, {'ReadOnlyVolume': False}]:
            info = self.mounted_info()
            info.update(change)
            with self.subTest(change=change), self.assertRaises(observer.Refused):
                observer.validate_mountpoint(info, identity)

    def test_actual_descriptor_reader_requires_readonly_fs_and_exact_single_file(self):
        report = observer.parse_fat(fixture_image())[1]
        root = SimpleNamespace(st_mode=stat.S_IFDIR | 0o500, st_dev=22)
        good = dict(st_mode=stat.S_IFREG | 0o400, st_dev=22, st_nlink=1, st_size=len(report), st_ino=99)
        def run_reader(file_changes=None, readonly=True):
            metadata = dict(good)
            metadata.update(file_changes or {})
            file = SimpleNamespace(**metadata)
            def fstat(fd):
                if fd in (10, 11):
                    return SimpleNamespace(st_dev=1)
                return root if fd == 12 else file
            with mock.patch.object(observer.os, 'open', side_effect=[10, 11, 12, 13]) as opened, \
                 mock.patch.object(observer.os, 'close'), mock.patch.object(observer.os, 'fstat', side_effect=fstat), \
                 mock.patch.object(observer.os, 'fstatvfs', return_value=SimpleNamespace(f_flag=os.ST_RDONLY if readonly else 0)), \
                 mock.patch.object(observer.os, 'read', side_effect=[report, b'']):
                result = observer.read_volume_report('/Volumes/RAMPROBE')
                for call in opened.call_args_list:
                    self.assertTrue(call.args[1] & os.O_NOFOLLOW)
                    self.assertEqual(call.args[1] & os.O_ACCMODE, os.O_RDONLY)
                self.assertEqual(opened.call_args_list[-1].args[0], 'REPORT.TXT')
                self.assertEqual(opened.call_args_list[-1].kwargs['dir_fd'], 12)
                return result
        self.assertTrue(run_reader()['filesystem_readonly'])
        for change in [{'st_mode': stat.S_IFDIR}, {'st_nlink': 2}, {'st_size': 1025}, {'st_dev': 23}]:
            with self.subTest(change=change), self.assertRaises(observer.Refused):
                run_reader(change)
        with self.assertRaises(observer.Refused):
            run_reader(readonly=False)

    def test_symlink_open_failure_is_not_followed(self):
        with mock.patch.object(observer.os, 'open', side_effect=[10, OSError('symlink refused')]), \
             mock.patch.object(observer.os, 'fstat', return_value=SimpleNamespace(st_dev=1)), \
             mock.patch.object(observer.os, 'close'):
            with self.assertRaises(OSError):
                observer.read_volume_report('/Volumes/RAMPROBE')

    def test_mountpoint_change_after_read_is_inconclusive(self):
        info = self.mounted_info()
        after = dict(info, MountPoint='/Volumes/OTHER')
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'trial'
            with mock.patch.object(sys, 'platform', 'darwin'), mock.patch('builtins.print'), \
                 mock.patch.object(observer, 'snapshot', side_effect=[[], fixture_tree(), fixture_tree(), fixture_tree(), fixture_tree()]), \
                 mock.patch.object(observer, 'command', side_effect=[plistlib.dumps(info), plistlib.dumps(info),
                     json.dumps(self.reader_details()).encode(), plistlib.dumps(after)]):
                self.assertEqual(observer.observe(output, 1, report_via_volume=True), 2)
                self.assertFalse(json.loads((output / 'result.json').read_text())['minimal_discriminator_positive'])

    def test_raw_permission_failure_does_not_fall_back_to_mount(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(sys, 'platform', 'darwin'), mock.patch('builtins.print'), \
                 mock.patch.object(observer, 'snapshot', side_effect=[[], fixture_tree(), fixture_tree()]), \
                 mock.patch.object(observer, 'command', side_effect=[plistlib.dumps(fixture_disk()),
                     PermissionError('fixture raw permission denial')]) as command:
                self.assertEqual(observer.observe(Path(directory) / 'trial', 1), 2)
                self.assertFalse(any('mount' in call.args[0] for call in command.call_args_list))


if __name__ == '__main__':
    unittest.main()
