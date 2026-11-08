#!/usr/bin/env python3
"""Two read-only preconditions only. No device mutation or automatic retry."""
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import socket
import struct
import subprocess
import sys
from datetime import datetime, timezone
import zlib

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT.parent / '2026-11-07-asus-stock-kernel-version-control/artifacts/original.img'
ADB = Path('/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools/adb')
SERIAL = 'DEVICE_SERIAL_REDACTED'
PINS = {
    'image': 'f0bf4834a2d3ec207590c6742d0adb4fd9a3adc9a2dab5d0ec7c28f27963b140',
    'raw_kernel': 'db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a',
    'adb': '1811e253b21b12cbfda7201ebaf86c10e7ddcb5c606a7a81f7c82b4c429c2d3b',
}
FLAGS = ['CONFIG_CONFIGFS_FS', 'CONFIG_USB_CONFIGFS',
         'CONFIG_USB_CONFIGFS_MASS_STORAGE', 'CONFIG_TMPFS']
evidence = {
    'observed_at_utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'Only the two delivered preconditions; no calibration or deployment approval.',
    'config': {'status': 'UNKNOWN', 'values': {flag: None for flag in FLAGS},
               'sha256': None, 'input': str(IMAGE), 'pins': PINS},
    'device': {'serial': SERIAL, 'status': 'UNKNOWN'},
    'udc': {'status': 'UNKNOWN', 'listing_attempts': 0},
    'missing_input': [],
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def one_gzip(data, limit):
    stream = zlib.decompressobj(31)
    raw = stream.decompress(data, limit + 1)
    require(len(raw) <= limit and stream.eof and not stream.unconsumed_tail,
            'Incomplete or oversized gzip stream')
    return raw, stream.unused_data


def save_config(raw, provenance, compressed=None):
    text = raw.decode('utf-8')
    require(text.startswith('#') and '\nCONFIG_' in text, 'Not a kernel config')
    values = {}
    for flag in FLAGS:
        matches = re.findall(r'^' + re.escape(flag) + r'=(.*)$', text, re.M)
        disabled = re.findall(r'^# ' + re.escape(flag) + r' is not set$', text, re.M)
        require(len(matches) + len(disabled) <= 1, 'Duplicate config value: ' + flag)
        values[flag] = matches[0] if matches else ('n' if disabled else 'absent')
    (ROOT / 'stock-3.18.35.config').write_bytes(raw)
    if compressed is not None:
        (ROOT / 'stock-3.18.35.config.gz').write_bytes(compressed)
    evidence['config'].update(status='EXACT_CONFIG', provenance=provenance,
                              sha256=sha(raw), bytes=len(raw), values=values,
                              all_required_builtin=all(v == 'y' for v in values.values()))
    (ROOT / 'selected-values.json').write_text(json.dumps(values, indent=2) + '\n')


def host_config():
    data = IMAGE.read_bytes()
    require(sha(data) == PINS['image'], 'Public control image hash mismatch')
    require(data[:8] == b'ANDROID!', 'Not Android boot format')
    ks, _, rs, _, ss, _, _, page = struct.unpack_from('<8I', data, 8)
    require(page == 2048 and ss == 0, 'Unexpected Android v0 layout')
    align = lambda n: (n + page - 1) // page * page
    kernel = data[page:page + ks]
    ramdisk = data[page + align(ks):page + align(ks) + rs]
    require(len(kernel) == ks and len(ramdisk) == rs, 'Truncated image')
    boot_id = hashlib.sha1(kernel + struct.pack('<I', ks) + ramdisk +
                          struct.pack('<II', rs, 0)).digest() + bytes(12)
    require(data[576:608] == boot_id, 'Android image ID mismatch')
    require(kernel[:4] == bytes.fromhex('88168858') and
            struct.unpack_from('<I', kernel, 4)[0] == ks - 512 and
            kernel[8:40].split(b'\0')[0] == b'KERNEL', 'Unexpected MTK wrapper')
    raw, fdt = one_gzip(kernel[512:], 64 * 1024 * 1024)
    require(sha(raw) == PINS['raw_kernel'], 'Decompressed actual stock Image hash mismatch')
    require(len(fdt) >= 40 and fdt[:4] == bytes.fromhex('d00dfeed') and
            struct.unpack_from('>I', fdt, 4)[0] == len(fdt), 'Unexpected appended FDT')
    evidence['config'].update(image_sha256=sha(data), raw_kernel_sha256=sha(raw),
                              raw_kernel_bytes=len(raw))
    starts = [m.start() for m in re.finditer(b'IKCFG_ST', raw)]
    evidence['config']['ikcfg_start_marker_count'] = len(starts)
    if not starts:
        evidence['config']['host_observation'] = 'No embedded IKCFG_ST; not a feature failure'
        return False
    require(len(starts) == 1, 'Ambiguous embedded config markers')
    offset = starts[0] + len(b'IKCFG_ST')
    config, trailing = one_gzip(raw[offset:], 4 * 1024 * 1024)
    require(trailing.startswith(b'IKCFG_ED'), 'Missing IKCFG_ED immediately after one gzip stream')
    consumed = len(raw[offset:]) - len(trailing)
    evidence['config'].update(ikcfg_start_offset=starts[0], gzip_bytes=consumed)
    save_config(config, 'Embedded IKCFG in pinned actual shipped stock 3.18.35 Image')
    return True


def exact_read(sock, count):
    result = b''
    while len(result) < count:
        part = sock.recv(count - len(result))
        require(bool(part), 'Existing ADB server closed version response')
        result += part
    return result


def verify_adb_server():
    require(sha(ADB.read_bytes()) == PINS['adb'], 'ADB executable hash mismatch')
    # A read-only version query verifies that server 5037 already exists and is
    # protocol-compatible, before adb could attempt automatic server startup.
    with socket.create_connection(('127.0.0.1', 5037), timeout=3) as sock:
        sock.sendall(b'000chost:version')
        require(exact_read(sock, 4) == b'OKAY', 'Existing ADB server rejected version query')
        size = int(exact_read(sock, 4), 16)
        require(size == 4, 'Unexpected existing ADB version framing')
        version = exact_read(sock, size).decode('ascii')
        require(version == '0029', 'Unexpected ADB server protocol; refuse client invocation')
    evidence['device']['adb_sha256'] = PINS['adb']
    evidence['device']['existing_server'] = {'port': 5037, 'protocol_version': version}


def shell_once(body):
    nonce = secrets.token_hex(16)
    start = ('PREFLIGHT_BEGIN_' + nonce + '\n').encode()
    footer_prefix = ('\nPREFLIGHT_END_' + nonce + ':').encode()
    command = "printf 'PREFLIGHT_BEGIN_%s\\n' '" + nonce + "'\n" + body
    command += "\nrc=$?\nprintf '\\nPREFLIGHT_END_%s:%s\\n' '" + nonce + "' \"$rc\"\n"
    env = dict(os.environ)
    env['ADB_SERVER_SOCKET'] = 'tcp:127.0.0.1:5037'
    try:
        result = subprocess.run([str(ADB), '-P', '5037', '-s', SERIAL,
                                 'shell', '-T', '-x', command],
                                capture_output=True, timeout=15, env=env)
    except subprocess.TimeoutExpired as error:
        return None, {'timeout_seconds': 15,
                      'stderr': (error.stderr or b'').decode('utf-8', 'replace')}
    record = {'host_exit': result.returncode, 'stderr': result.stderr.decode('utf-8', 'replace'),
              'nonce': nonce}
    # Old stock shell framing can return 255. Trust only a complete, exact
    # fresh frame with remote success, and permit no other host exit code.
    footer = re.search(re.escape(footer_prefix) + rb'([0-9]+)\n$', result.stdout)
    framed = (result.returncode in (0, 255) and result.stdout.startswith(start)
              and footer is not None and result.stdout.count(start) == 1
              and result.stdout.count(footer_prefix) == 1)
    record['complete_frame'] = framed
    record['remote_exit'] = int(footer.group(1)) if framed else None
    record['remote_stderr_transport'] = 'Merged into stdout by legacy shell -x'
    valid = framed and record['remote_exit'] == 0 and not result.stderr
    record['complete_success_frame'] = valid
    if not valid:
        record['stdout'] = result.stdout.decode('utf-8', 'replace')
        return None, record
    return result.stdout[len(start):footer.start()], record


def device_checks(need_config):
    verify_adb_server()
    fields = [
        ('serial', 'getprop ro.serialno'), ('device', 'getprop ro.product.device'),
        ('sdk', 'getprop ro.build.version.sdk'), ('boot_completed', 'getprop sys.boot_completed'),
        ('adb_secure', 'getprop ro.adb.secure'), ('selinux', 'getenforce'),
        ('kernel', 'uname -r'), ('boot_uuid', 'cat /proc/sys/kernel/random/boot_id'),
    ]
    body = '\n'.join("printf '" + name + "='; " + command + ' || exit $?' for name, command in fields)
    payload, observation = shell_once(body)
    evidence['device']['identity_transport'] = observation
    require(payload is not None, 'Identity read unavailable or incomplete; no UDC listing attempted')
    lines = payload.decode('ascii').splitlines()
    require(len(lines) == len(fields), 'Unexpected identity record count')
    identity = {}
    for line, (name, _) in zip(lines, fields):
        require(line.startswith(name + '='), 'Unexpected identity framing')
        identity[name] = line[len(name) + 1:]
    evidence['device']['identity'] = identity
    expected = {'serial': SERIAL, 'device': 'P00A_2', 'sdk': '24', 'boot_completed': '1',
                'adb_secure': '1', 'selinux': 'Enforcing', 'kernel': '3.18.35'}
    require(all(identity[k] == v for k, v in expected.items()), 'Unexpected hardware/stock identity; stopped')
    require(re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', identity['boot_uuid']),
            'Invalid fresh boot UUID')
    evidence['device']['status'] = 'EXPECTED_STOCK_IDENTITY'
    evidence['device']['previously_verified_boot_uuid'] = '3525090a-4d53-4ec6-b704-7ba459bdc610'
    evidence['udc']['listing_attempts'] = 1
    payload, observation = shell_once('LC_ALL=C ls -1 /sys/class/udc')
    evidence['udc']['transport'] = observation
    if payload is not None:
        names = payload.decode('utf-8').splitlines()
        require(all(re.fullmatch(r'[A-Za-z0-9_.:+-]+', name) for name in names),
                'Unexpected controller directory listing format')
        evidence['udc'].update(status='OBSERVED', names=names, count=len(names),
                               exactly_one=len(names) == 1)
    else:
        evidence['missing_input'].append('Complete permitted /sys/class/udc directory listing')
    if need_config:
        payload, observation = shell_once('cat /proc/config.gz')
        evidence['config']['device_transport'] = observation
        if payload is None:
            evidence['missing_input'].append('Exact shipped 3.18.35 kernel config')
            return
        config, trailing = one_gzip(payload, 4 * 1024 * 1024)
        require(not trailing, 'Unexpected bytes after device config gzip stream')
        save_config(config, 'Unprivileged /proc/config.gz on freshly verified stock identity', payload)


def main():
    need_config = True
    try:
        need_config = not host_config()
    except Exception as error:
        evidence['config']['error'] = str(error)
        # A malformed or mismatched public input is not permission to seek alternatives.
        evidence['missing_input'].append('Validated exact public stock kernel config input')
        need_config = False
    try:
        device_checks(need_config)
    except Exception as error:
        evidence['device']['error'] = str(error)
        evidence['missing_input'].append('Completed read-only checks on expected stock device')
    cfg = evidence['config']
    if cfg['status'] == 'EXACT_CONFIG' and not cfg['all_required_builtin']:
        result = 'FAIL_FOR_UNSUPPORTED_FEATURE'
        decision = 'Do not run reporter C on this stock control: at least one required builtin is absent.'
    elif cfg.get('all_required_builtin') and evidence['udc'].get('exactly_one'):
        result = 'PASS_ONLY_FOR_THESE_TWO_PRECONDITIONS'
        decision = 'These two checks pass; the incomplete consultation does not authorize calibration or deployment.'
    else:
        result = 'UNKNOWN_INPUT_REQUIRED'
        if evidence['udc'].get('count') is not None and evidence['udc']['count'] != 1:
            evidence['udc']['precondition_failure'] = 'Controller count must be exactly one; no corrective action authorized.'
        decision = ('Stop before calibration; parent must supply the exact shipped 3.18.35 config.'
                    if cfg['status'] != 'EXACT_CONFIG' else
                    'Stop before calibration; parent must resolve the recorded missing or unmet precondition.')
    evidence['result'] = result
    evidence['next_decision'] = decision
    (ROOT / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps({'result': result, 'config': cfg['values'],
                      'udc_count': evidence['udc'].get('count'), 'next_decision': decision}))


if __name__ == '__main__':
    main()
