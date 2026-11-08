import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('observer', ROOT / 'source/observer.py')
o = importlib.util.module_from_spec(spec)
spec.loader.exec_module(o)
RUN = '142cf5d3-b649-4334-90a5-d71b6137ff65'
STOCK_ROW = dict(serial=o.STOCK, state='device', usb='17895424X', product='WW_P00A',
                 model='P00A', device='P00A_2', transport_id='17')
PROBE_ROW = dict(serial=o.PROBE, state='recovery', usb='17895424X', product='p00a_diagnostic',
                 model='P00A_RAM_diagnostic', device='p00a', transport_id='18')


def pin(now=None):
    return dict(schema=1, run_id=RUN, profile=o.PROFILE, candidate_sha256=o.IMAGE_SHA,
                padded_sha256=o.PADDED_SHA, created_at=time.time() if now is None else now,
                observer_sha256=o.sha(Path(o.__file__).read_bytes()), stock=copy.deepcopy(STOCK_ROW),
                properties=copy.deepcopy(o.PROPS), enforcing=True)


def report(changes=None):
    sections = {p: 'observed' for p in o.PATHS}
    sections.update({'/proc/version': 'Linux version 4.9.337 (builder@host) #1 SMP',
                     '/proc/cmdline': 'console=tty0 androidboot.serialno=' + o.STOCK + ' initrd=0x44000200,0x11f7b0',
                     '/proc/uptime': '24.03 19.91',
                     '/proc/mounts': 'rootfs / rootfs rw 0 0\nproc /proc proc rw 0 0\nadb /dev/usb-ffs/adb functionfs rw 0 0',
                     '/sys/fs/selinux/enforce': '1', '/proc/self/attr/current': 'u:r:recovery:s0\0',
                     '/sys/class/udc/musb-hdrc/state': 'configured', '/config/usb_gadget/g1/UDC': 'musb-hdrc'})
    sections.update({'entries ' + p: 'entry' for p in o.DIRS})
    sections[o.LABELS[-1]] = 'syslog result=-13'
    sections.update(changes or {})
    text = o.PREFIX + 'No block-device opens, mounts, module loads or peripheral control.\n'
    for label in o.LABELS:
        text += '\n[ ' + label + ' ]\n' + sections[label] + '\n'
    return (text + '\nEND_DIAGNOSTIC\n').encode()


class ReportTests(unittest.TestCase):
    def test_success_has_no_hardware_or_directory_claim(self):
        result = o.validate_report(report(), 0)
        self.assertTrue(result['report_collected'])
        self.assertTrue(result['diagnostic_requirements_passed'])
        self.assertTrue(result['partial_measurements'])
        self.assertFalse(result['hardware_ready'])
        self.assertEqual(result['measurements']['entries /sys/class/udc'], 'unverified_listing')

    def test_optional_battery_error_is_unavailable(self):
        result = o.validate_report(report({'/sys/class/power_supply/battery/uevent': 'read errno=5'}), 0)
        self.assertTrue(result['diagnostic_requirements_passed'])
        self.assertEqual(result['measurements']['/sys/class/power_supply/battery/uevent'], 'unavailable')
        self.assertFalse(result['hardware_ready'])

    def test_mandatory_failures(self):
        cases = [('/proc/version', 'Linux version 3.18.35'), ('/proc/version', 'read errno=5'),
                 ('/proc/cmdline', 'androidboot.serialno=' + o.STOCK + 'WRONG initrd=0x44000200,0x11f7b0'),
                 ('/proc/cmdline', 'androidboot.serialno=' + o.STOCK + ' initrd=0x44000200,0x11f7b0 initrd=0x44000200,0x11f7b0'),
                 ('/proc/cmdline', 'androidboot.serialno=' + o.STOCK + ' androidboot.serialno=other initrd=0x44000200,0x11f7b0'),
                 ('/proc/cmdline', 'open errno=13'), ('/sys/fs/selinux/enforce', '0'),
                 ('/proc/self/attr/current', 'u:r:shell:s0'), ('/proc/uptime', '2.00 1.00'),
                 ('/proc/uptime', '301.00 100.00'), ('/proc/uptime', 'nan 1.0'),
                 ('/sys/class/udc/musb-hdrc/state', 'not attached'), ('/config/usb_gadget/g1/UDC', 'other'),
                 ('/proc/mounts', '/dev/block/mmcblk0p25 /system ext4 ro 0 0'),
                 ('/proc/mounts', 'data /data f2fs rw 0 0'), ('/proc/mounts', '[bounded read limit reached]')]
        for path, value in cases:
            with self.subTest(path=path, value=value):
                self.assertFalse(o.validate_report(report({path: value}), 0)['diagnostic_requirements_passed'])

    def test_framing_and_exit_faults(self):
        data = report()
        for value in [b'open errno=13\n', data[:-20], data + b'trailing', data + data,
                      data.replace(o.MARKER.encode(), b'ASUS RAM-only diagnostic os-rescue-v1'),
                      data.replace(b'[ /proc/version ]', b'[ /proc/cmdline ]'),
                      data.replace(b'[ /proc/version ]\n', b'[ /proc/version ]\n[ /proc/version ]\n'),
                      data.replace(b'Linux version', b'\xffLinux version')]:
            with self.subTest(value=value[:50]):
                self.assertFalse(o.validate_report(value, 0)['diagnostic_requirements_passed'])
        self.assertFalse(o.validate_report(data, 74)['diagnostic_requirements_passed'])


class PinSelectionTests(unittest.TestCase):
    def test_pin_age_and_binding(self):
        p = pin(1000)
        o.validate_pin(p, RUN, now=1180)
        for changed in [dict(created_at=999), dict(created_at=1182), dict(profile='old'),
                        dict(candidate_sha256='bad'), dict(observer_sha256='bad'),
                        dict(run_id='other'), dict(enforcing=False), dict(properties={})]:
            with self.subTest(changed=changed), self.assertRaises(o.Refused):
                o.validate_pin({**p, **changed}, RUN, now=1181)

    def test_exact_probe_and_inventory_ambiguity(self):
        p = pin()
        self.assertEqual(o.select([PROBE_ROW], p), PROBE_ROW)
        for rows in [[PROBE_ROW, STOCK_ROW], [{**PROBE_ROW, 'serial': '0123456789ABCDEF'}],
                     [{**PROBE_ROW, 'usb': 'other'}], [{**PROBE_ROW, 'model': 'P00A_RAM_49_probe'}],
                     [{**PROBE_ROW, 'transport_id': '0'}], [{**PROBE_ROW, 'state': 'device'}]]:
            with self.subTest(rows=rows), self.assertRaises(o.Refused):
                o.select(rows, p)

    def test_inventory_parser(self):
        row = ' '.join([PROBE_ROW['serial'], PROBE_ROW['state']] + [k + ':' + v for k, v in PROBE_ROW.items() if k not in ('serial', 'state')])
        self.assertEqual(o.parse_devices('List of devices attached\n' + row), [PROBE_ROW])
        for text in [row + '\n' + row, row + ' usb:other', '* daemon started successfully *', row + ' broken']:
            with self.subTest(text=text), self.assertRaises(o.Refused):
                o.parse_devices(text)

    def test_transport_rechecked_and_targeted(self):
        calls = []
        row_text = 'P00A49PROBE recovery usb:17895424X product:p00a_diagnostic model:P00A_RAM_diagnostic device:p00a transport_id:18\n'
        def runner(args, **kwargs):
            calls.append(args)
            return subprocess.CompletedProcess(args, 0, row_text.encode() if args[1] == 'devices' else report(), b'')
        result = o.Adb(runner).target(PROBE_ROW, ['shell', 'report'], pin())
        self.assertEqual(result.stdout, report())
        self.assertEqual(calls, [['adb', 'devices', '-l'], ['adb', '-t', '18', 'shell', 'report'], ['adb', 'devices', '-l']])

    def test_changed_enumeration_refuses(self):
        calls = []
        def runner(args, **kwargs):
            calls.append(args)
            return subprocess.CompletedProcess(args, 0, b'P00A49PROBE recovery usb:17895424X product:p00a_diagnostic model:P00A_RAM_diagnostic device:p00a transport_id:19\n', b'')
        with self.assertRaises(o.Refused):
            o.Adb(runner).target(PROBE_ROW, ['shell', 'report'], pin())
        self.assertEqual(len(calls), 1)


class LifecycleTests(unittest.TestCase):
    class FakeAdb:
        def __init__(self, data, error=None):
            self.rows = iter([STOCK_ROW, PROBE_ROW, STOCK_ROW])
            self.data = data
            self.error = error

        def inventory(self):
            return [next(self.rows)]

        def target(self, row, command, pin=None):
            if command == ['shell', 'report']:
                if self.error:
                    raise o.Refused(self.error)
                return subprocess.CompletedProcess([], 0, self.data, b'')
            if command[-1] == 'getenforce':
                data = b'Enforcing\n'
            else:
                data = (o.PROPS[command[-1]] + '\n').encode()
            return subprocess.CompletedProcess([], 0, data, b'')

    def run_observer(self, data, error=None):
        with tempfile.TemporaryDirectory(dir=ROOT / 'tests') as tmp:
            return o.observe(self.FakeAdb(data, error), pin(), RUN, Path(tmp), sleep=lambda _: None)

    def test_stock_return_without_valid_report_never_passes(self):
        result = self.run_observer(b'open errno=13\n')
        self.assertTrue(result['stock_returned'])
        self.assertFalse(result['report_collected'])
        self.assertFalse(result['overall_accepted'])
        self.assertEqual(result['status'], 'FAILED_OR_INCOMPLETE')

    def test_valid_report_return_still_needs_actual_restoration(self):
        result = self.run_observer(report())
        self.assertTrue(result['diagnostic_requirements_passed'])
        self.assertTrue(result['stock_returned'])
        self.assertFalse(result['stock_recovery_readback_verified'])
        self.assertFalse(result['overall_accepted'])
        self.assertEqual(result['status'], 'AWAITING_STOCK_RECOVERY_READBACK')

    def test_transport_error_stops_without_retry(self):
        result = self.run_observer(report(), 'transport lost')
        self.assertIn('transport lost', result['observer_error'])
        self.assertFalse(result['stock_returned'])
        self.assertFalse(result['overall_accepted'])

    def test_default_plan_never_runs_adb(self):
        for phase in ['pin', 'observe', 'finalize']:
            proc = subprocess.run(['python3', '-B', str(ROOT / 'source/observer.py'), phase], capture_output=True)
            self.assertEqual(proc.returncode, 0)
            self.assertFalse(json.loads(proc.stdout)['device_contacted'])

    def test_exact_frozen_bytes_verified(self):
        self.assertEqual(o.verify_image()['candidate_sha256'], o.IMAGE_SHA)
        with tempfile.NamedTemporaryFile(dir=ROOT / 'tests') as tmp:
            tmp.write(b'wrong'); tmp.flush()
            with self.assertRaises(o.Refused):
                o.verify_image(Path(tmp.name))

    def test_final_acceptance_requires_current_full_stock_bytes_and_same_run(self):
        stock = o.WORKSPACE / '2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin'
        p = pin()
        result = self.run_observer(report())
        # The observer fixture used a separate pin; bind explicitly to this fixture's pin.
        result['pin_sha256'] = o.object_sha(p)
        with tempfile.TemporaryDirectory(dir=ROOT / 'tests') as tmp:
            directory = Path(tmp)
            (directory / result['report_file']).write_bytes(report())
            readback = directory / 'full-stock-p10.bin'
            readback.write_bytes(stock.read_bytes())
            adb = self.FakeAdb(report())
            accepted = o.finalize(adb, p, RUN, result, directory, readback)
            self.assertTrue(accepted['overall_accepted'])
            self.assertTrue(accepted['stock_recovery_readback_verified'])
            self.assertFalse(accepted['hardware_ready'])
            for changes in [dict(run_id='other'), dict(pin_sha256='other'),
                            dict(stock_returned=False), dict(status='FAILED_OR_INCOMPLETE')]:
                with self.subTest(changes=changes), self.assertRaises(o.Refused):
                    o.finalize(self.FakeAdb(report()), p, RUN, {**result, **changes}, directory, readback)
            os.utime(readback, (p['created_at'] - 10, p['created_at'] - 10))
            with self.assertRaises(o.Refused):
                o.finalize(self.FakeAdb(report()), p, RUN, result, directory, readback)
            readback.write_bytes(bytes(o.SIZE))
            with self.assertRaises(o.Refused):
                o.finalize(self.FakeAdb(report()), p, RUN, result, directory, readback)
            readback.write_bytes(b'partial')
            with self.assertRaises(o.Refused):
                o.finalize(self.FakeAdb(report()), p, RUN, result, directory, readback)
            readback.write_bytes(stock.read_bytes())
            (directory / result['report_file']).write_bytes(report() + b'changed')
            with self.assertRaises(o.Refused):
                o.finalize(self.FakeAdb(report()), p, RUN, result, directory, readback)


if __name__ == '__main__':
    unittest.main()
