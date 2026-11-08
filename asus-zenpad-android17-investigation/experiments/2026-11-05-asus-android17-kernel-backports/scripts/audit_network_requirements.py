#!/usr/bin/env python3
"""Audit pinned platform versus kernel sources on Linux; never claim runtime support.

The token comparisons are conservative source-level gaps. Header declarations
alone do not prove an implementation or successful BPF verifier execution.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess

platform = Path('/srv/android/lineage24')
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--candidate', choices=['erofs', 'network', 'ids', 'fd'], default='erofs')
args = parser.parse_args()
kernel_root = Path('/srv/android/asus-android17')
kernel = kernel_root / {'erofs': 'kernel', 'network': 'kernel-network', 'ids': 'kernel-bpf-ids', 'fd': 'kernel-bpf-fd'}[args.candidate]
donor = Path('/srv/android/reference-kernel')
out = kernel_root / 'logs' / {'erofs': 'network-capability-audit.json', 'network': 'network-enabled-capability-audit.json', 'ids': 'bpf-ids-capability-audit.json', 'fd': 'bpf-fd-capability-audit.json'}[args.candidate]

def revision(path):
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path, text=True).strip()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def constants(text, prefix):
    return set(re.findall(r'\b' + prefix + r'[A-Z][A-Z_0-9]*\b', text))

loader_path = platform / 'packages/modules/Connectivity/bpf/loader/NetBpfLoad.cpp'
utils_path = platform / 'packages/modules/Connectivity/bpf/headers/include/bpf/KernelUtils.h'
uapi = kernel / 'include/uapi/linux/bpf.h'
assert revision(donor) == 'a668db21f3cfddc5b73f081c6bb532b1b3351b36'
# The reference checkout is sparse. Read its pinned Git blob without expanding
# or changing its working tree.
donor_uapi = subprocess.check_output(['git', 'show', 'HEAD:include/uapi/linux/bpf.h'], cwd=donor)
config_path = kernel_root / {'erofs': 'build-erofs', 'network': 'build-network', 'ids': 'build-bpf-ids', 'fd': 'build-bpf-fd'}[args.candidate] / '.config'
config = {}
for line in config_path.read_text().splitlines():
    if line.startswith('CONFIG_') and '=' in line:
        key, value = line.split('=', 1)
        config[key] = value
    match = re.fullmatch(r'# (CONFIG_\w+) is not set', line)
    if match:
        config[match.group(1)] = 'n'

required_config = [
    'CONFIG_64BIT', 'CONFIG_BPF', 'CONFIG_BPF_SYSCALL', 'CONFIG_CGROUP_BPF',
    'CONFIG_BPF_JIT', 'CONFIG_HAVE_EBPF_JIT', 'CONFIG_BPF_JIT_ALWAYS_ON',
    'CONFIG_NET_CLS_BPF', 'CONFIG_NET_CLS_MATCHALL', 'CONFIG_NET_ACT_BPF',
    'CONFIG_NET_ACT_POLICE', 'CONFIG_HAVE_EFFICIENT_UNALIGNED_ACCESS',
]
source_paths = [loader_path]
source_paths += sorted((platform / 'packages/modules/Connectivity/bpf/progs').glob('*.c'))
source_paths += sorted((platform / 'packages/modules/Connectivity/bpf/netd').rglob('*.cpp'))
source_paths += sorted((platform / 'packages/modules/Connectivity/bpf/syscall_wrappers').rglob('*.h'))
source_tokens = set()
for source in source_paths:
    source_tokens |= constants(source.read_text(), 'BPF_')
current_tokens = constants(uapi.read_text(), 'BPF_')
donor_tokens = constants(donor_uapi.decode(), 'BPF_')
commands = ['BPF_PROG_GET_NEXT_ID', 'BPF_MAP_GET_NEXT_ID', 'BPF_PROG_GET_FD_BY_ID',
            'BPF_MAP_GET_FD_BY_ID', 'BPF_OBJ_GET_INFO_BY_FD', 'BPF_PROG_QUERY',
            'BPF_BTF_LOAD', 'BPF_MAP_FREEZE', 'BPF_LINK_CREATE']

report = {
    'scope': 'source and compiled-config audit only; not runtime validation',
    'platform_connectivity_revision': revision(platform / 'packages/modules/Connectivity'),
    'kernel_revision': revision(kernel),
    'donor_revision': revision(donor),
    'source_hashes': {str(path): digest(path) for path in [loader_path, utils_path, uapi, config_path]},
    'donor_uapi_sha256': hashlib.sha256(donor_uapi).hexdigest(),
    'sdk37_kernel_floor': {'version': '5.10', 'source': str(utils_path),
                          'status': '4.9 candidate does not meet unmodified platform requirement'},
    'later_26q4_floor': {'version': '5.15', 'source': str(loader_path),
                       'note': 'conditional on runtime release flags; not assumed for initial SDK 37'},
    'config': {key: config.get(key, 'absent') for key in required_config},
    'unprivileged_bpf_default_off': config.get('CONFIG_BPF_UNPRIV_DEFAULT_OFF', 'absent'),
    'command_declarations': {key: {'candidate': key in current_tokens, 'donor': key in donor_tokens} for key in commands},
    'reserved_without_implementation': ['BPF_PROG_TEST_RUN'] if args.candidate in ['ids', 'fd'] else [],
    'platform_constants_missing_from_candidate': sorted(source_tokens - current_tokens),
    'missing_constants_present_in_donor': sorted((source_tokens - current_tokens) & donor_tokens),
    'limitations': [
        'Text references include conditional and optional paths; not all missing tokens are unconditional requirements.',
        'Constants may be declared by another header; presence/absence here is not an implementation proof.',
        'Do not set ro.bpf.kver_override or edit version checks as a substitute for tested feature backports.',
        'No kernel, BPF object or Android binary has been run on the tablet by this audit.',
    ],
}
out.parent.mkdir(exist_ok=True, parents=True)
out.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: report[key] for key in ['kernel_revision', 'config', 'command_declarations']}, indent=2))
print(f'Saved {out}')
