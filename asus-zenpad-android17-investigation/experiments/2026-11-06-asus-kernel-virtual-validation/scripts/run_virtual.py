#!/usr/bin/env python3
"""Run a bounded ARM64 VM with no disks, networking or physical USB devices."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--candidate', choices=['baseline', 'ids', 'fd', 'meta'], default='baseline')
args = parser.parse_args()
root = Path('/srv/android/asus-virtual-validation')
if args.candidate != 'baseline':
    root = root / args.candidate
assert (root / 'logs/build-complete').exists()
image = root / 'build/arch/arm64/boot/Image'
initramfs = root / 'initramfs.cpio.gz'
log = root / 'logs/qemu-boot.log'
assert not log.exists(), 'Keep prior runtime evidence'
command = ['qemu-system-aarch64', '-machine', 'virt,gic-version=3', '-cpu', 'cortex-a53',
           '-smp', '2', '-m', '1024', '-nographic', '-monitor', 'none', '-no-reboot',
           '-nic', 'none', '-kernel', str(image), '-initrd', str(initramfs),
           '-append', 'console=ttyAMA0 earlycon=pl011,0x9000000 rdinit=/init panic=-1 loglevel=7']
timed_out = False
with log.open('x') as stream:
    try:
        result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=stream,
                                stderr=subprocess.STDOUT, timeout=180 if args.candidate in ['fd', 'meta'] else 120)
        returncode = result.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        returncode = None
text = log.read_text(errors='replace')
matches = re.findall(r'ASUS_BPF_SMOKE (\{[^\r\n]+\})', text)
smoke = json.loads(matches[0]) if len(matches) == 1 else None
id_matches = re.findall(r'ASUS_BPF_IDS (\{[^\r\n]+\})', text)
ids = json.loads(id_matches[0]) if len(id_matches) == 1 else None
fd_matches = re.findall(r'ASUS_BPF_FD (\{[^\r\n]+\})', text)
fd_checks = json.loads(fd_matches[0]) if len(fd_matches) == 1 else None
meta_matches = re.findall(r'ASUS_BPF_META (\{[^\r\n]+\})', text)
meta = json.loads(meta_matches[0]) if len(meta_matches) == 1 else None
report = {'scope': 'Generic code in ARM64 QEMU only; no ASUS hardware validation',
          'qemu_command': command, 'qemu_returncode': returncode, 'timed_out': timed_out,
          'source': json.loads((root / 'source-provenance.json').read_text()),
          'artifacts': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in [image, initramfs, root / 'init', root / 'build/.config']},
          'smoke': smoke, 'smoke_completed': 'ASUS_VIRTUAL_SMOKE_DONE' in text,
          'ids': ids,
          'fd_checks': fd_checks,
          'metadata_checks': meta,
          'basic_bpf_passed': bool(smoke and smoke['basic_failures'] == 0),
          'android17_networking_validated': False,
          'hardware_runtime_validated': False}
(root / 'logs/qemu-result.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
assert not timed_out and returncode == 0, 'Virtual boot did not power off cleanly'
assert report['smoke_completed'] and report['basic_bpf_passed'], 'Basic virtual BPF smoke failed'
if args.candidate != 'baseline':
    assert ids and ids['all_checks_passed'], 'BPF ID lifecycle/permission tests failed'
if args.candidate in ['fd', 'meta']:
    assert fd_checks and fd_checks['all_checks_passed'], 'Lookup-by-ID tests failed'
if args.candidate == 'meta':
    assert meta and meta['all_checks_passed'], 'Tag/JIT metadata tests failed'
