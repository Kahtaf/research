"""Execute the exact parser fragment with no external utilities in PATH."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/service'))
import transport as T

BATTERY = dict(POWER_SUPPLY_BATT_VOL='4000', POWER_SUPPLY_PRESENT='1',
               POWER_SUPPLY_HEALTH='Good', POWER_SUPPLY_CAPACITY='80', POWER_SUPPLY_BATT_TEMP='250')
CASES = []


class ShellGuards(unittest.TestCase):
    def run_guard(self, *, battery=None, usb='POWER_SUPPLY_ONLINE=1\n', mounts=None, command=False):
        with tempfile.TemporaryDirectory(dir=ROOT / 'tests') as directory:
            p = Path(directory)
            batt = battery if battery is not None else ''.join(k + '=' + v + '\n' for k, v in BATTERY.items())
            (p / 'battery').write_text(batt)
            (p / 'usb').write_text(usb)
            (p / 'mounts').write_text(mounts if mounts is not None else '/dev/block/mmcblk0p24 /cache ext4 rw 0 0\n')
            if command:
                (p / 'recovery').mkdir()
                (p / 'recovery/command').write_text('')
            script = T.CACHE_AND_POWER_CHECKS
            for old, new in [('/proc/mounts', str(p / 'mounts')),
                             ('/sys/class/power_supply/battery/uevent', str(p / 'battery')),
                             ('/sys/class/power_supply/usb/uevent', str(p / 'usb')),
                             ('/cache/recovery', str(p / 'recovery'))]:
                script = script.replace(old, new)
            # Canonical path lookup is the only external boundary replaced here;
            # the fixture's source is already a canonical path. All parsing and
            # threshold decisions execute the production shell fragment.
            prefix = 'set -eu\nPATH=/nonexistent\nreadlink() { [ "$1" = -f ]; printf "%s\\n" "$2"; }\n'
            result = subprocess.run(['/bin/sh', '-c', prefix + script], capture_output=True, text=True, timeout=3)
            CASES.append(dict(exit=result.returncode, awk_available=False, device_contacted=False))
            return result.returncode

    def test_valid_and_threshold_boundaries_without_awk(self):
        self.assertNotIn('awk', T.METADATA_GUARDS)
        self.assertEqual(self.run_guard(), 0)
        for key, values in [('POWER_SUPPLY_BATT_VOL', ['3700', '4500']),
                            ('POWER_SUPPLY_CAPACITY', ['50', '100']),
                            ('POWER_SUPPLY_BATT_TEMP', ['100', '450'])]:
            for value in values:
                row = dict(BATTERY)
                row[key] = value
                self.assertEqual(self.run_guard(battery=''.join(k + '=' + v + '\n' for k, v in row.items())), 0)

    def test_missing_and_duplicate_required_keys_refused(self):
        for key in BATTERY:
            missing = ''.join(k + '=' + v + '\n' for k, v in BATTERY.items() if k != key)
            duplicate = ''.join(k + '=' + v + '\n' for k, v in BATTERY.items()) + key + '=' + BATTERY[key] + '\n'
            self.assertNotEqual(self.run_guard(battery=missing), 0)
            self.assertNotEqual(self.run_guard(battery=duplicate), 0)
        for usb in ['', 'POWER_SUPPLY_ONLINE=1\nPOWER_SUPPLY_ONLINE=1\n', 'POWER_SUPPLY_ONLINE=0\n']:
            self.assertNotEqual(self.run_guard(usb=usb), 0)

    def test_malformed_and_out_of_range_numbers_refused(self):
        for key, bad in [('POWER_SUPPLY_BATT_VOL', ['3699', '4501', '-1', '+4000', '4e3', '04000', '9999999', '']),
                         ('POWER_SUPPLY_CAPACITY', ['49', '101', '-1', '+80', '80x', '080', '9999999', '']),
                         ('POWER_SUPPLY_BATT_TEMP', ['99', '451', '-1', '+250', '2.5', '0250', '9999999', ''])]:
            for value in bad:
                row = dict(BATTERY)
                row[key] = value
                self.assertNotEqual(self.run_guard(battery=''.join(k + '=' + v + '\n' for k, v in row.items())), 0)

    def test_mount_identity_and_command_file_guards(self):
        for mounts in ['', '/dev/block/mmcblk0p24 /cache ext4 rw 0 0\n' * 2,
                       '/dev/block/mmcblk0p25 /cache ext4 rw 0 0\n',
                       '/dev/block/mmcblk0p24 /cache f2fs rw 0 0\n',
                       '/dev/block/mmcblk0p24 /cache ext4 rw 0 0 EXTRA\n']:
            self.assertNotEqual(self.run_guard(mounts=mounts), 0)
        self.assertNotEqual(self.run_guard(command=True), 0)

    def test_health_and_presence_must_match(self):
        for key, value in [('POWER_SUPPLY_PRESENT', '0'),
                           ('POWER_SUPPLY_HEALTH', 'Overheat'),
                           ('POWER_SUPPLY_HEALTH', 'Good ')]:
            row = dict(BATTERY)
            row[key] = value
            self.assertNotEqual(self.run_guard(battery=''.join(k + '=' + v + '\n' for k, v in row.items())), 0)


if __name__ == '__main__':
    result = unittest.main(exit=False)
    (ROOT / 'evidence/shell-guard-cases.json').write_text(json.dumps(dict(
        tests=result.result.testsRun, cases=len(CASES), all_passed=result.result.wasSuccessful(),
        scope='Actual production parsing/threshold fragment under host POSIX shell; readlink canonicalization mocked; no Android node guards executed',
        device_contacted=False), indent=2) + '\n')
    raise SystemExit(not result.result.wasSuccessful())
