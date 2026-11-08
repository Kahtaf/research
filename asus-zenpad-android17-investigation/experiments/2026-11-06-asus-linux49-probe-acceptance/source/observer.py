#!/usr/bin/env python3
"""Read-only, exact-candidate observation. No device contact without --execute."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
IMAGE = WORKSPACE / '2026-11-06-asus-android17-build-continuation/artifacts/probe-r2/UNTESTED-combined-linux49-ram-probe.img'
IMAGE_SHA = '48bb6efa1620cb380037e53b53cfa560e38cd23b95211c8634616ce94fd6ce48'
PADDED_SHA = '25812e7dde39ec37e3f4c9438341cc29f2b2e7dce61e4b88d0886cd9dd075b16'
STOCK_RECOVERY_SHA = '902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
SIZE = 16740352
STOCK = 'DEVICE_SERIAL_REDACTED'
PROBE = 'P00A49PROBE'
FINGERPRINT = 'asus/WW_P00A/P00A_2:7.0/NRD90M/WW_P00A-V5.3.20-20180809:user/release-keys'
PROFILE = 'asus-p00a2-combined-linux49-ram-probe-r2-exact-v1'
MARKER = 'ASUS RAM-only diagnostic combined-linux49-r1'
ENDPOINT = 'REPORT_ENDPOINT uid=2000 context=u:r:shell:s0'
PREFIX = ENDPOINT + '\n\n[ /tmp/diagnostic.txt ]\n' + MARKER + '\n'
PATHS = ['/proc/version', '/proc/cmdline', '/proc/uptime', '/proc/meminfo',
         '/proc/mounts', '/proc/filesystems', '/proc/partitions',
         '/proc/bus/input/devices', '/proc/interrupts', '/sys/fs/selinux/enforce',
         '/proc/self/attr/current', '/sys/class/graphics/fb0/name',
         '/sys/class/graphics/fb0/virtual_size', '/sys/class/power_supply/battery/uevent',
         '/sys/class/power_supply/usb/uevent', '/sys/class/udc/musb-hdrc/state',
         '/config/usb_gadget/g1/UDC']
DIRS = ['/sys/class/udc', '/sys/class/input', '/sys/class/thermal',
        '/sys/class/power_supply', '/sys/class/graphics']
LABELS = PATHS + ['entries ' + p for p in DIRS] + ['kernel ring, last <=32768 bytes; may be denied']
PROPS = {'ro.serialno': STOCK, 'ro.build.fingerprint': FINGERPRINT,
         'ro.build.version.sdk': '24', 'sys.boot_completed': '1',
         'ro.adb.secure': '1', 'ro.product.device': 'P00A_2'}


class Refused(Exception):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def object_sha(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def check(condition, message):
    if not condition:
        raise Refused(message)


def verify_image(path=IMAGE):
    data = path.read_bytes()
    check(len(data) == 8880128 and sha(data) == IMAGE_SHA, 'Frozen r2 image changed')
    check(sha(data + bytes(SIZE - len(data))) == PADDED_SHA, 'Padded image mismatch')
    return {'profile': PROFILE, 'candidate_sha256': IMAGE_SHA, 'padded_sha256': PADDED_SHA}


def parse_devices(text):
    rows = []
    for line in text.splitlines():
        if not line or line == 'List of devices attached':
            continue
        words = line.split()
        check(len(words) >= 2 and not words[0].startswith('*'), 'Unexpected inventory line')
        row = dict(serial=words[0], state=words[1])
        for word in words[2:]:
            check(':' in word, 'Malformed inventory field')
            key, value = word.split(':', 1)
            check(key not in row and bool(value), 'Duplicate/empty inventory field')
            row[key] = value
        rows.append(row)
    check(len({r['serial'] for r in rows}) == len(rows), 'Duplicate serial')
    ids = [r['transport_id'] for r in rows if 'transport_id' in r]
    check(len(set(ids)) == len(ids), 'Duplicate transport ID')
    return rows


def select(rows, pin=None):
    candidates = [r for r in rows if r['serial'] in (STOCK, PROBE) or
                  (pin is not None and r.get('usb') == pin['stock']['usb'])]
    check(len(candidates) <= 1, 'Ambiguous inventory')
    if not candidates:
        return None
    row = candidates[0]
    check(bool(row.get('usb')), 'Physical USB topology required')
    check(re.fullmatch('[1-9][0-9]*', row.get('transport_id', '')), 'Current transport ID required')
    if pin is not None:
        check(row['usb'] == pin['stock']['usb'], 'USB topology changed')
    if row['serial'] == PROBE:
        expected = dict(state='recovery', product='p00a_diagnostic', model='P00A_RAM_diagnostic', device='p00a')
    else:
        check(row['serial'] == STOCK, 'Unexpected device at pinned USB port')
        expected = dict(state='device', device='P00A_2')
        if pin is not None:
            expected.update({k: pin['stock'][k] for k in ('product', 'model')})
        else:
            check(bool(row.get('product')) and bool(row.get('model')), 'Missing stock identity')
    check(all(row.get(k) == v for k, v in expected.items()), 'Identity/state mismatch')
    return row


class Adb:
    def __init__(self, runner=subprocess.run):
        self.runner = runner

    def run(self, args):
        result = self.runner(['adb', *args], capture_output=True, timeout=12)
        check(len(result.stdout) <= 300000 and len(result.stderr) <= 16384, 'Oversized ADB output')
        return result

    def inventory(self):
        result = self.run(['devices', '-l'])
        check(result.returncode == 0 and not result.stderr, 'ADB inventory failure')
        return parse_devices(result.stdout.decode('utf-8', 'strict'))

    def target(self, row, command, pin=None):
        check(select(self.inventory(), pin) == row, 'Enumeration changed before operation')
        result = self.run(['-t', row['transport_id'], *command])
        check(select(self.inventory(), pin) == row, 'Enumeration changed during operation')
        check(not result.stderr, 'ADB transport/endpoint error; no retry')
        return result


def stock_checks(adb, row, pin=None):
    for prop, expected in PROPS.items():
        result = adb.target(row, ['shell', 'getprop', prop], pin)
        check(result.returncode == 0 and result.stdout.decode().strip() == expected,
              'Stock preflight property failed: ' + prop)
    result = adb.target(row, ['shell', 'getenforce'], pin)
    check(result.returncode == 0 and result.stdout.strip() == b'Enforcing', 'Stock not enforcing')


def make_pin(adb, run_id, now=None):
    check(str(uuid.UUID(run_id)) == run_id, 'Canonical run UUID required')
    row = select(adb.inventory())
    check(row is not None and row['serial'] == STOCK, 'Start in exact stock Android')
    stock_checks(adb, row)
    return {**verify_image(), 'schema': 1, 'run_id': run_id, 'created_at': time.time() if now is None else now,
            'observer_sha256': sha(Path(__file__).read_bytes()), 'stock': row,
            'properties': PROPS, 'enforcing': True}


def validate_pin(pin, run_id, now=None, max_age=180):
    now = time.time() if now is None else now
    check(str(uuid.UUID(run_id)) == run_id and pin.get('run_id') == run_id, 'Run binding mismatch')
    check(pin.get('profile') == PROFILE and pin.get('candidate_sha256') == IMAGE_SHA and
          pin.get('padded_sha256') == PADDED_SHA, 'Candidate/profile binding mismatch')
    check(pin.get('observer_sha256') == sha(Path(__file__).read_bytes()), 'Observer changed since preflight')
    check(isinstance(pin.get('created_at'), (int, float)) and
          0 <= now - pin['created_at'] <= max_age, 'Stale/future preflight')
    check(pin.get('properties') == PROPS and pin.get('enforcing') is True, 'Missing exact stock preflight')
    check(select([pin['stock']], pin)['serial'] == STOCK, 'Invalid stock pin')


def validate_report(data, returncode):
    result = {'report_collected': False, 'diagnostic_requirements_passed': False,
              'measurements': {}, 'hardware_ready': False, 'errors': []}
    try:
        check(returncode == 0, 'Report endpoint returned failure')
        check(len(data) <= 262144 and len(data) > 0, 'Report length invalid')
        text = data.decode('utf-8', 'strict')
        check(text.startswith(PREFIX), 'Exact endpoint/marker framing missing')
        check(text.endswith('\nEND_DIAGNOSTIC\n'), 'Terminal framing missing')
        check(text.count(ENDPOINT) == text.count(MARKER) == text.count('END_DIAGNOSTIC') == 1,
              'Duplicate framing')
        headers = list(re.finditer(r'^\[ (.+) \]\n', text, re.MULTILINE))
        check([m[1] for m in headers] == ['/tmp/diagnostic.txt'] + LABELS,
              'Missing, duplicate, reordered or injected section')
        sections = {}
        for i, header in enumerate(headers[1:], 1):
            end = headers[i + 1].start() if i + 1 < len(headers) else text.rindex('\nEND_DIAGNOSTIC\n')
            sections[header[1]] = text[header.end():end].strip('\n')
        result['report_collected'] = True
        for path in PATHS:
            body = sections[path]
            failure = (not body or re.search(r'(?:open|read) errno=|bounded read limit reached', body))
            result['measurements'][path] = 'unavailable' if failure else 'observed'
        for path in DIRS:
            # Frozen getdents silently drops errors: listing transport cannot certify completeness.
            result['measurements']['entries ' + path] = 'unverified_listing'
        required = ['/proc/version', '/proc/cmdline', '/proc/uptime', '/proc/mounts',
                    '/sys/fs/selinux/enforce', '/proc/self/attr/current',
                    '/sys/class/udc/musb-hdrc/state', '/config/usb_gadget/g1/UDC']
        check(all(result['measurements'][p] == 'observed' for p in required), 'Mandatory observation unavailable')
        check(re.match(r'^Linux version 4\.9\.337(?:\s|[-+])', sections['/proc/version']), 'Wrong kernel release')
        tokens = sections['/proc/cmdline'].split()
        for key, expected in [('androidboot.serialno', STOCK), ('initrd', '0x44000200,0x11f7b0')]:
            matches = [token.split('=', 1)[1] for token in tokens if token.startswith(key + '=')]
            check(matches == [expected], 'Missing, wrong or duplicate cmdline ' + key)
        check(sections['/sys/fs/selinux/enforce'] == '1', 'SELinux not enforcing')
        check(sections['/proc/self/attr/current'].rstrip('\0') == 'u:r:recovery:s0', 'Collector context mismatch')
        check(sections['/config/usb_gadget/g1/UDC'] == 'musb-hdrc', 'Wrong UDC binding')
        check(sections['/sys/class/udc/musb-hdrc/state'] == 'configured', 'USB not configured')
        uptime = sections['/proc/uptime'].split()
        check(len(uptime) == 2 and all(re.fullmatch(r'[0-9]+\.[0-9]+', x) for x in uptime), 'Invalid uptime')
        check(20 <= float(uptime[0]) <= 300, 'Stale/premature diagnostic uptime')
        mounts = sections['/proc/mounts'].splitlines()
        check(bool(mounts), 'No mount observations')
        allowed = {'rootfs', 'proc', 'sysfs', 'tmpfs', 'devpts', 'selinuxfs', 'configfs', 'functionfs'}
        for mount in mounts:
            fields = mount.split()
            check(len(fields) == 6 and fields[2] in allowed and not fields[0].startswith('/dev/block'),
                  'Unexpected persistent/unknown mount')
        result['diagnostic_requirements_passed'] = True
    except (Refused, UnicodeError, ValueError) as error:
        result['errors'].append(str(error))
    result['partial_measurements'] = any(v != 'observed' for v in result['measurements'].values())
    return result


def observe(adb, pin, run_id, out, clock=time.monotonic, sleep=time.sleep):
    validate_pin(pin, run_id)
    verify_image()
    first = select(adb.inventory(), pin)
    check(first is not None and first['serial'] == STOCK, 'Observer must start in stock before trial entry')
    check(first == pin['stock'], 'Stock enumeration changed since pin; create a new pin')
    stock_checks(adb, first, pin)
    started = time.time()
    state = {'schema': 1, 'run_id': run_id, 'pin_sha256': object_sha(pin),
             'profile': PROFILE, 'candidate_sha256': IMAGE_SHA, 'started_at': started,
             'report_collected': False, 'diagnostic_requirements_passed': False,
             'stock_returned': False, 'stock_recovery_readback_verified': False,
             'overall_accepted': False, 'hardware_ready': False}
    seen = False
    report_attempted = False
    deadline = clock() + 420
    try:
        with (out / 'events.jsonl').open('x') as log:
            while clock() < deadline:
                row = select(adb.inventory(), pin)
                event = {'at': time.time(), 'row': row}
                if row and row['serial'] == PROBE:
                    seen = True
                    if not report_attempted:
                        report = adb.target(row, ['shell', 'report'], pin)
                        # A not-yet-published report is an endpoint result, not a transport failure.
                        assessment = validate_report(report.stdout, report.returncode)
                        name = 'report-' + str(time.time_ns()) + '.txt'
                        (out / name).write_bytes(report.stdout)
                        event.update(report_file=name, sha256=sha(report.stdout), assessment=assessment)
                        state.update(assessment)
                        not_ready = report.stdout == (ENDPOINT + '\n\n[ /tmp/diagnostic.txt ]\nopen errno=2\n').encode()
                        report_attempted = not not_ready
                        if assessment['report_collected']:
                            state.update(report_file=name, report_sha256=sha(report.stdout), report_at=event['at'])
                elif row and seen:
                    stock_checks(adb, row, pin)
                    state.update(stock_returned=True, returned_at=time.time(), returned_stock=row)
                    event['stock_returned'] = True
                log.write(json.dumps(event, sort_keys=True) + '\n')
                log.flush()
                if state['stock_returned']:
                    break
                sleep(2)
        check(state['stock_returned'], 'Observation deadline; physical fallback may be required')
    except (Refused, subprocess.TimeoutExpired, OSError, UnicodeError) as error:
        state['observer_error'] = str(error)
    state['completed_at'] = time.time()
    state['status'] = 'AWAITING_STOCK_RECOVERY_READBACK' if (state['stock_returned'] and
                      state['diagnostic_requirements_passed']) else 'FAILED_OR_INCOMPLETE'
    return state


def finalize(adb, pin, run_id, observation, observation_dir, readback):
    validate_pin(pin, run_id, max_age=1200)
    check(observation.get('run_id') == run_id and observation.get('pin_sha256') == object_sha(pin), 'Observation run mismatch')
    check(observation.get('profile') == PROFILE and observation.get('candidate_sha256') == IMAGE_SHA, 'Observation profile mismatch')
    check(observation.get('status') == 'AWAITING_STOCK_RECOVERY_READBACK' and not observation.get('observer_error'), 'Observation incomplete')
    check(observation.get('stock_returned') is True, 'No stock return')
    check(pin['created_at'] <= observation['started_at'] <= observation['returned_at'] <= observation['completed_at'] <= time.time(), 'Observation chronology invalid')
    report_name = observation['report_file']
    check(Path(report_name).name == report_name, 'Invalid report path')
    report = (observation_dir / report_name).read_bytes()
    check(sha(report) == observation['report_sha256'] and
          validate_report(report, 0)['diagnostic_requirements_passed'], 'Saved report changed/invalid')
    # The readback origin is a parent-operated full-p10 read, not inferred from return.
    stat = readback.stat()
    check(readback.is_file() and stat.st_size == SIZE, 'Full p10 readback required')
    check(observation['returned_at'] <= stat.st_mtime <= time.time(), 'Readback predates return or is future-dated')
    check(sha(readback.read_bytes()) == STOCK_RECOVERY_SHA, 'Stock recovery readback mismatch')
    row = select(adb.inventory(), pin)
    check(row is not None and row['serial'] == STOCK, 'Exact stock must still be present')
    stock_checks(adb, row, pin)
    return {**observation, 'stock_recovery_readback_verified': True, 'overall_accepted': True,
            'status': 'DIAGNOSTIC_AND_STOCK_RESTORATION_ACCEPTED',
            'readback_sha256': STOCK_RECOVERY_SHA, 'readback_bytes': SIZE,
            'readback_provenance': 'Parent-supplied post-return full-p10 capture; byte-verified here',
            'finalized_at': time.time(), 'hardware_ready': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['pin', 'observe', 'finalize', 'validate-report', 'verify-image'])
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--run-id')
    parser.add_argument('--pin', type=Path)
    parser.add_argument('--observation', type=Path)
    parser.add_argument('--readback', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.phase == 'verify-image':
        print(json.dumps(verify_image(), indent=2))
        return 0
    if args.phase == 'validate-report':
        check(args.report is not None, '--report required')
        result = validate_report(args.report.read_bytes(), 0)
        print(json.dumps(result, indent=2))
        return 0 if result['diagnostic_requirements_passed'] else 2
    if not args.execute:
        print(json.dumps({'mode': 'PLAN_ONLY', 'phase': args.phase, 'profile': PROFILE,
                          'device_contacted': False, 'writer_implemented': False}))
        return 0
    check(args.out is not None and args.run_id is not None, '--out and --run-id required')
    check(ROOT in args.out.resolve().parents, 'Output must remain in this spike')
    args.out.mkdir(mode=0o700, parents=True, exist_ok=False)
    adb = Adb()
    if args.phase == 'pin':
        result = make_pin(adb, args.run_id)
        name = 'pin.json'
        code = 0
    else:
        check(args.pin is not None, '--pin required')
        pin = json.loads(args.pin.read_text())
        if args.phase == 'observe':
            result = observe(adb, pin, args.run_id, args.out)
            name = 'observation.json'
            # Incomplete until separate actual restoration/readback acceptance.
            code = 2
        else:
            check(args.observation is not None and args.readback is not None, '--observation and --readback required')
            result = finalize(adb, pin, args.run_id, json.loads(args.observation.read_text()), args.observation.parent, args.readback)
            name = 'acceptance.json'
            code = 0
    (args.out / name).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return code


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (Refused, OSError, KeyError, ValueError, subprocess.TimeoutExpired) as error:
        print(json.dumps({'status': 'REFUSED', 'error': str(error), 'overall_accepted': False}))
        raise SystemExit(2)
