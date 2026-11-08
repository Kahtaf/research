#!/usr/bin/env python3
"""On-demand ASUS root shell, with enforcing restored on normal shell exit.

Reads commands from stdin. No daemon, boot-image patch or app is installed.
The checked binary was preserved by mtk-easy-su in December 2020; the original
author's download host is unavailable. Its pinned LFS hash is recorded locally.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
commands = sys.stdin.read()
binary = root / 'sources/mtk-su-mirror-b'
expected = '328632e853ff6427af9f35cb83a91d9e960f35d01188ee66d46ae9c7ce7c7827'
if hashlib.sha256(binary.read_bytes()).hexdigest() != expected:
    raise SystemExit('Root binary hash mismatch')
adb = ['adb', '-s', 'DEVICE_SERIAL_REDACTED']
for prop, value in [
    ('ro.product.device', 'P00A_2'), ('ro.build.version.sdk', '24'),
    ('ro.build.fingerprint', 'asus/WW_P00A/P00A_2:7.0/NRD90M/WW_P00A-V5.3.20-20180809:user/release-keys'),
]:
    actual = subprocess.check_output(adb + ['shell', 'getprop', prop], text=True, timeout=10).strip()
    if actual != value:
        raise SystemExit(f'Unexpected {prop}: {actual}')
subprocess.run(adb + ['push', str(binary), '/data/local/tmp/asus-mtk-su64'], check=True, stdout=sys.stderr, timeout=15)
subprocess.run(adb + ['shell', 'chmod', '700', '/data/local/tmp/asus-mtk-su64'], check=True, timeout=10)
script = "trap 'setenforce 1' EXIT\n[ \"$(id -u)\" = 0 ] || exit 93\n" + commands + '\n'
result = subprocess.run(adb + ['shell', 'timeout 60 /data/local/tmp/asus-mtk-su64 -c /system/bin/sh'], input=script, text=True, timeout=75)
state = subprocess.check_output(adb + ['shell', 'getenforce'], text=True, timeout=10).strip()
if state != 'Enforcing':
    raise SystemExit('SELinux was not restored; inspect the root session immediately')
raise SystemExit(result.returncode)
