#!/usr/bin/env python3
"""Exact-device, on-demand stock root over an already authenticated LAN ADB link."""
from pathlib import Path
import hashlib
import ipaddress
import re
import secrets
import subprocess
import sys

WORKSPACE = Path(__file__).resolve().parents[2]
ENDPOINT = 'DEVICE_SERIAL_REDACTED'
SERIAL = 'DEVICE_SERIAL_REDACTED'
ADB = ['adb', '-s', ENDPOINT]
BINARY = WORKSPACE / '2026-11-05-asus-root-hardware-validation/sources/mtk-su-mirror-b'
BINARY_HASH = '328632e853ff6427af9f35cb83a91d9e960f35d01188ee66d46ae9c7ce7c7827'
REMOTE_BINARY = '/data/local/tmp/asus-mtk-su64'
PROPS = {'ro.serialno': SERIAL, 'ro.product.device': 'P00A_2',
         'ro.build.version.sdk': '24',
         'ro.build.fingerprint': 'asus/WW_P00A/P00A_2:7.0/NRD90M/WW_P00A-V5.3.20-20180809:user/release-keys',
         'ro.adb.secure': '1', 'sys.boot_completed': '1'}

def query(args):
    return subprocess.check_output(ADB + args, text=True, timeout=12).strip()

def main():
    commands = sys.stdin.read()
    if ENDPOINT != SERIAL or ADB != ['adb', '-s', SERIAL]:
        raise SystemExit('Exact pinned USB transport required')
    if not BINARY.is_file() or BINARY.is_symlink() or hashlib.sha256(BINARY.read_bytes()).hexdigest() != BINARY_HASH:
        raise SystemExit('Root binary identity mismatch')
    if query(['get-serialno']) != ENDPOINT:
        raise SystemExit('Transport endpoint mismatch')
    for prop, expected in PROPS.items():
        if query(['shell', 'getprop', prop]) != expected:
            raise SystemExit('Stock identity mismatch: ' + prop)
    if query(['shell', 'getenforce']) != 'Enforcing':
        raise SystemExit('Expected Enforcing before root')
    precheck = '''set -eu
[ ! -L /data ]
[ ! -L /data/local ]
[ ! -L /data/local/tmp ]
[ "$(stat -c '%u:%g:%a' /data)" = 1000:1000:771 ]
[ "$(stat -c '%u:%g:%a' /data/local)" = 0:0:751 ]
[ "$(stat -c '%u:%g:%a' /data/local/tmp)" = 2000:2000:771 ]
p=/data/local/tmp/asus-mtk-su64
[ ! -L "$p" ]
if [ -e "$p" ]; then
[ -f "$p" ]
[ "$(stat -c '%u:%g:%a:%h' "$p")" = 2000:2000:700:1 ]
fi'''
    subprocess.run(ADB + ['shell', precheck], check=True, timeout=12)
    subprocess.run(ADB + ['push', str(BINARY), REMOTE_BINARY], check=True,
                   stdout=sys.stderr, timeout=20)
    subprocess.run(ADB + ['shell', 'chmod', '700', REMOTE_BINARY], check=True, timeout=12)
    token = secrets.token_hex(16)
    script = "trap 'setenforce 1' EXIT\n[ \"$(id -u)\" = 0 ] || exit 93\n(\nset -eu\n" + commands + (
        '\n)\nasus_wifi_rc=$?\nprintf "\\nASUS_WIFI_ROOT_' + token + '=%s\\n" "$asus_wifi_rc"\nexit "$asus_wifi_rc"\n')
    result = subprocess.run(ADB + ['shell', 'timeout 60 '+REMOTE_BINARY+' -c /system/bin/sh'],
                            input=script, text=True, capture_output=True, timeout=75)
    if query(['shell', 'getenforce']) != 'Enforcing':
        raise SystemExit('Enforcing restoration unverified; inspect this session')
    matches = re.findall(r'^ASUS_WIFI_ROOT_'+token+r'=(\d{1,3})\r?$', result.stdout, re.M)
    sys.stdout.write(re.sub(r'\nASUS_WIFI_ROOT_'+token+r'=\d{1,3}\r?\n', '\n', result.stdout))
    sys.stderr.write(result.stderr)
    if len(matches) != 1 or not 0 <= int(matches[0]) <= 255:
        raise SystemExit('Missing/ambiguous inner status; stop without retry')
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    return int(matches[0])

if __name__ == '__main__':
    raise SystemExit(main())
