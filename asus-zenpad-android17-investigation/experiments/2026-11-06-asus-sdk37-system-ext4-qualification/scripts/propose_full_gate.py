#!/usr/bin/env python3
"""Read completed owner receipts and headers, then emit a deferred kernel mount plan."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from check_system_header import inspect, need

KERNEL_SHA = 'c59e030cdfc3e752eeddbbf62d091ae9760c94d5fbf780a22824e004ec872080'
FIXTURE = Path('/srv/android/asus-sdk37-system-ext4-qualification-20261106/fixture-r2')


def main():
    import resource
    if hasattr(os, 'sched_setaffinity'):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
        resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--complete', required=True, type=Path)
    parser.add_argument('--system-image', required=True, type=Path)
    parser.add_argument('--guest-initrd', required=True, type=Path,
                        help='Future reviewed full-image observer; specimen initrd is unsuitable')
    args = parser.parse_args()
    receipt_bytes = args.complete.read_bytes()
    owner = json.loads(receipt_bytes)
    need(owner.get('elf_init_policy_neverallows_vintf_apex_host_checks_passed') is True,
         'Require terminal successful owner validation receipt')
    raw = owner['raw_system']
    need(raw['bytes'] == 3753902080 and raw['all_zero_ranges_written'] is True,
         'Require owner materialized final raw partition')
    need(len(raw['sha256']) == 64 and len(owner['source_system_sha256']) == 64,
         'Missing owner artifact digests')
    original_header = inspect(str(args.system_image), 3753902080)
    raw_header = inspect(raw['path'], 3753902080)
    need(raw_header['format'] == 'raw' and raw_header['file_bytes'] == raw['bytes'],
         'Owner raw artifact size/type mismatch')
    need(raw_header['superblock_sha256'] == original_header['superblock_sha256'] and
         raw_header['filesystem_bytes'] == original_header['filesystem_bytes'],
         'Original and owner raw superblocks differ')
    kernel = FIXTURE / 'Image'
    need(hashlib.sha256(kernel.read_bytes()).hexdigest() == KERNEL_SHA, 'Kernel pin mismatch')
    initrd_sha = hashlib.sha256(args.guest_initrd.read_bytes()).hexdigest()
    cmd = [str(FIXTURE / 'bin/qemu-system-aarch64'), '-machine', 'virt,gic-version=3',
           '-cpu', 'cortex-a53', '-accel', 'tcg,thread=single,tb-size=16',
           '-smp', '1', '-m', '384', '-nographic', '-monitor', 'none',
           '-no-reboot', '-nic', 'none', '-kernel', str(kernel), '-initrd', str(args.guest_initrd),
           '-blockdev', json.dumps({'driver': 'file', 'filename': raw['path'],
                                   'node-name': 'system-file', 'read-only': True}),
           '-blockdev', json.dumps({'driver': 'raw', 'file': 'system-file',
                                   'node-name': 'system-raw', 'read-only': True}),
           '-device', 'virtio-blk-device,drive=system-raw',
           '-append', 'console=ttyAMA0 rdinit=/init panic=-1 loglevel=7 selinux=0']
    print(json.dumps(dict(proposal_only=True, header_checks_pass=True,
                         actual_kernel_mount_passed=False, physical_GO=False,
                         owner_complete_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
                         owner_raw_sha256=raw['sha256'],
                         owner_original_sha256=owner['source_system_sha256'],
                         owner_image_digests_rehashed_here=False,
                         original_header=original_header, raw_header=raw_header,
                         kernel_sha256=KERNEL_SHA, observer_initrd_sha256=initrd_sha,
                         qemu_argv=cmd,
                         required_limits=dict(host_cpu_affinity_count=1, process_as_bytes=1024**3,
                                              process_cpu_seconds=60, wall_seconds=90),
                         acceptance_contract='FINAL-SYSTEM-GATE.md'), indent=2))


if __name__ == '__main__':
    main()
