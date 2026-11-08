#!/usr/bin/env python3
"""Parent-executed, one-shot integration. No wait, retry, rollback or detached launch."""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from continuation import terminal, preserve, apply, continuation_inputs
from r3_inputs import SENSOR_SUFFIX, sensor_selection, source_composition, platform_selection, platform_destinations, apply_platform, verify_bundle, complete_kernel

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILES = {
    'input/Goodix_Capacitive_TouchScreen.idc': 'ff9c53351559ea415c5bbb2aafd3472bbedd6f264646903d20189e41da2d8a55',
    'input/mtk-kpd.kl': 'a940764c7807d582cb04cadeb3140566d6472353cf27a31a52a2e7aefcb0a942',
    'input/input-mapping.mk': '6ec0030412932f6dcef9795aa9d708425661ff2368282b6b4536e03f743c1a75',
}
INPUT_SUFFIX = b'\n$(call inherit-product, device/asus/p00a/input/input-mapping.mk)\n'

class Refusal(RuntimeError):
    pass

def need(condition, message):
    if not condition:
        raise Refusal(message)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def write(path, data):
    with Path(path).open('x') as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())

def item(path):
    p = Path(path)
    if p.is_symlink():
        return {'symlink': os.readlink(p)}
    return {'sha256': sha(p)} if p.is_file() else None

def manifest(path):
    p = Path(path)
    return {str(f.relative_to(p)): item(f) for f in sorted(p.rglob('*'))
            if f.is_file() or f.is_symlink()}

def safe(root, relative):
    p = Path(relative)
    need(not p.is_absolute() and '..' not in p.parts, 'Unsafe relative input')
    target = Path(root) / p
    need(target.parent.resolve().is_relative_to(Path(root).resolve()), 'Symlink parent escape: ' + str(target))
    return target

def verify_pins(root):
    pins = read(root / 'inputs/kit-pins.json')
    actual = {str(p.relative_to(root)) for folder in ['scripts', 'inputs'] for p in (root / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p != root / 'inputs/kit-pins.json'}
    expected = {rel for rel in pins if rel.startswith(('scripts/', 'inputs/'))}
    need(actual == expected, 'Kit file set changed')
    for rel, digest in pins.items():
        p = safe(root, rel)
        need(not p.is_symlink() and sha(p) == digest, 'Kit pin changed: ' + rel)
    return sha(root / 'inputs/kit-pins.json')

def native_processes(plan):
    names = {'soong_ui', 'soong_build', 'ckati', 'siso', 'ninja', 'ninja-build'}
    rows = []
    # Inspect process identity, not an advisory state/ready file. Keep arguments out of reports.
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            pid = int(proc.name)
            comm = (proc / 'comm').read_text().strip()
            stat = (proc / 'stat').read_text().split(') ', 1)[1].split()
            state = stat[0]
            args = (proc / 'cmdline').read_bytes().replace(b'\0', b' ')
            supervisor = b'build_full_product.sh r5' in args and comm in {'bash', 'sh'}
            if state != 'Z' and (comm in names or supervisor or pid in plan['original_pids']):
                rows.append({'pid': pid, 'comm': comm, 'state': state, 'start_ticks': int(stat[19]), 'exe': os.readlink(proc / 'exe')})
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    return sorted(rows, key=lambda x: x['pid'])

def acquire(plan):
    # r+ requires the real existing lock; never creates, truncates or replaces its inode.
    lock = Path(plan['lock']).open('r+')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        raise Refusal('LIVE_BUILD_LOCK: original full-product lock is held')
    return lock

def revision_unused(plan):
    need(plan['revision'] == 'r9', 'Reviewed next revision changed')
    need(not list(Path(plan['logs']).glob('full-build-' + plan['revision'] + '.*')), 'Revision already used; never overwrite or relaunch')
    need(not (Path(plan['run_root']) / 'attempt').exists(), 'Previous attempt exists; partial failure stops permanently')

def input_selection(plan, staged, radio):
    delta = read(plan['input_mapping_receipt'])
    need(delta['files'] == INPUT_FILES, 'Input mapping selection changed')
    base = Path(plan['input_mapping_base']).read_bytes()
    need(hashlib.sha256(base).hexdigest() == delta['device_mk_before_sha256'] == radio['after']['device.mk']['sha256'],
         'Input base differs from reviewed radio device.mk')
    need(b'input/input-mapping.mk' not in base, 'Input mapping already inherited in base')
    candidate = Path(plan['staging']) / 'product-device'
    prior = (Path(plan['previous_product_inputs']) / 'device.mk').read_bytes()
    actual = (candidate / 'device.mk').read_bytes()
    need(prior == base + INPUT_SUFFIX and actual == prior + SENSOR_SUFFIX and delta['suffix'].encode() == INPUT_SUFFIX,
         'Input inheritance must be one exact additive line')
    need(hashlib.sha256(prior).hexdigest() == delta['device_mk_after_sha256'] == read(plan['previous_staged_receipt'])['product_after']['device.mk']['sha256'],
         'Input device.mk postimage mismatch')
    for rel, digest in INPUT_FILES.items():
        need(item(candidate / rel) == {'sha256': digest} == staged['product_after'].get(rel),
             'Input mapping bytes differ: ' + rel)
        need(rel not in staged['product_before'] and rel not in radio['after'], 'Unexpected preexisting input mapping')
    return set(INPUT_FILES)

def audit_inputs(plan, baseline=True):
    for path, digest in plan['external_pins'].items():
        need(sha(path) == digest, 'External artifact changed: ' + path)
    s = read(plan['staged_receipt'])
    parity = read(plan['parity_receipt'])
    source = read(plan['source_receipt'])
    old = read(plan['radio_receipt'])
    net = read(plan['network_receipt'])
    need(parity['firstboot_file_locking_parity_accepted'] is True, 'Parent scoped parity missing')
    need(parity['combined_kernel_sha256'] == s['product_after']['prebuilt/Image.gz-dtb']['sha256'], 'Parity kernel mismatch')
    need(parity['parent_actual_source_and_config_check']['staged_config_sha256'] == s['kernel_config_sha256'], 'Parity config mismatch')
    need(len(old['changes']) == 25 and len(source['changes']) == 276, 'Wrong reviewed source/radio selection')
    need(manifest(Path(plan['staging']) / 'product-device') == s['product_after'], 'Candidate product manifest mismatch')
    need(manifest(Path(plan['staging']) / 'platform-connectivity') == s['connectivity'], 'Candidate Connectivity manifest mismatch')
    need(set(net['connectivity_after']) == {'bpf/loader/NetBpfLoad.cpp', 'bpf/netd/BpfHandler.cpp', 'bpf/progs/netd.c'}, 'Connectivity11 selection mismatch')
    need(s['connectivity'] == {k: {'sha256': v} for k, v in net['connectivity_after'].items()}, 'Connectivity receipt mismatch')
    continuation_inputs(plan)
    from artifact import check_preimage, REL
    check_preimage(safe(plan['aosp'],REL))
    need(manifest(plan['device']) == read(plan['staged_receipt'])['product_after'], 'Already-integrated r8 device preimage mismatch')
    changes = {k for k in s['product_before'].keys() | s['product_after'].keys() if s['product_before'].get(k) != s['product_after'].get(k)}
    inputs = input_selection(plan, s, old)
    sensors = sensor_selection(plan, s)
    source_composition(plan, source)
    platforms = platform_selection(plan, phase='after')
    supplement_files = verify_bundle(plan)
    need(changes == set(old['changes']) | {'BoardConfig.mk', 'prebuilt/Image.gz-dtb'} | inputs | sensors | {'connectivity/src/driver_cmd_p00a.c', 'sepolicy/vendor/file_contexts'}, 'Product change selection mismatch')
    need(s['product_before'] == old['before'], 'Radio original preimages differ')
    for rel in old['changes']:
        if rel not in ('BoardConfig.mk', 'device.mk', 'rootdir/ueventd.rc', 'connectivity/src/driver_cmd_p00a.c', 'sepolicy/vendor/file_contexts'):
            need(s['product_after'][rel] == old['after'][rel], 'Radio postimage differs: ' + rel)
    for rel, digest in net['connectivity_after'].items():
        need(item(safe(plan['connectivity'], rel)) == {'sha256': digest}, 'Connectivity preimage mismatch: ' + rel)
    need(item(plan['wificond']) == s['product_after']['radio/wificond.rc'], 'wificond preimage mismatch')
    need(sha(plan['defconfig']) == s['kernel_config_sha256'], 'Already-integrated config drift')
    need(Path(plan['kernel_link']).resolve() == Path(plan['kernel']), 'Active kernel source link changed')
    need(sha(plan['patch']) == source['patch_sha256'], 'Patch/source receipt mismatch')
    for rel, change in source['changes'].items():
        expected = {'sha256': change['after']}
        need(item(safe(plan['kernel'], rel)) == expected, 'Kernel preimage mismatch: ' + rel)
        need(item(safe(plan['compiled_fixture'], rel)) == {'sha256': change['after']}, 'Compiled fixture postimage mismatch: ' + rel)
    count = 0
    if baseline:
        snapshot = read(plan['snapshot'])
        head = subprocess.check_output(['git', '-C', plan['kernel'], 'rev-parse', 'HEAD'], text=True).strip()
        need(head == snapshot['head'] == source['base_commit'], 'Active kernel base changed')
        tracked = subprocess.check_output(['git', '-C', plan['kernel'], 'ls-files', '--cached', '--others', '--exclude-standard', '-z']).decode().strip('\0').split('\0')
        selected = {p for p in tracked if safe(plan['kernel'], p).is_file()}
        need(selected == set(snapshot['files']) | set(source['changes']) | {str(Path(plan['defconfig']).relative_to(plan['kernel']))}, 'Active kernel source set differs from frozen baseline')
        for rel, digest in snapshot['files'].items():
            need(item(safe(plan['kernel'], rel)) == {'sha256': source['changes'].get(rel, {}).get('after', digest)}, 'Integrated baseline mismatch: ' + rel)
            count += 1
        need(count == 61976, 'Incomplete baseline')
        compiled_count = complete_kernel(plan)
    return {'active_baseline_files': count, 'kernel_postimages': 276, 'radio_changes': 25,
            'total_product_changes': len(changes), 'input_mapping_files': len(inputs), 'sensor_source_files': len(sensors), 'platform_source_files': len(platforms), 'qualified_bpf_files': supplement_files, 'complete_compiled_files': compiled_count if baseline else None, 'connectivity_files': 3, 'scoped_parity': True,
            'full_service_chain_accepted': False, 'flash_ready': False}

def verify_integrated(plan, baseline=False):
    s = read(plan['staged_receipt'])
    source = read(plan['source_receipt'])
    need(manifest(plan['device']) == s['product_after'], 'Integrated product drift')
    need(sha(plan['defconfig']) == s['kernel_config_sha256'], 'Integrated config drift')
    post = {}
    for rel, change in source['changes'].items():
        actual = item(safe(plan['kernel'], rel))
        need(actual == {'sha256': change['after']}, 'Integrated source drift: ' + rel)
        post[rel] = actual
    for rel, expected in s['connectivity'].items():
        need(item(safe(plan['connectivity'], rel)) == expected, 'Integrated Connectivity drift: ' + rel)
    need(item(plan['wificond']) == s['product_after']['radio/wificond.rc'], 'Integrated wificond drift')
    count = 0
    if baseline:
        snapshot = read(plan['snapshot'])
        for rel, before in snapshot['files'].items():
            expected = source['changes'].get(rel, {}).get('after', before)
            need(item(safe(plan['kernel'], rel)) == {'sha256': expected}, 'Integrated baseline drift: ' + rel)
            count += 1
        tracked = subprocess.check_output(['git', '-C', plan['kernel'], 'ls-files', '--cached', '--others', '--exclude-standard', '-z']).decode().strip('\0').split('\0')
        selected = {p for p in tracked if safe(plan['kernel'], p).is_file()}
        allowed = set(snapshot['files']) | set(source['changes']) | {str(Path(plan['defconfig']).relative_to(plan['kernel']))}
        need(selected == allowed, 'Integrated source set drift')
    continuation_inputs(plan)
    need(Path(plan['kernel_link']).resolve() == Path(plan['kernel']), 'Kernel source link drift')
    snapshot = read(plan['snapshot'])
    need(subprocess.check_output(['git','-C',plan['kernel'],'rev-parse','HEAD'],text=True).strip() == snapshot['head'] == source['base_commit'], 'Kernel base HEAD drift')
    platforms = platform_selection(plan, phase='after')
    sensor_selection(plan, s)
    return {'platform_sources': platforms, 'source_postimages': post, 'baseline_files_verified': count,
            'config_sha256': sha(plan['defconfig']), 'connectivity': s['connectivity'],
            'wificond': item(plan['wificond']), 'full_service_chain_accepted': False}


def copy_exact(src, dst, expected):
    need(not Path(dst).is_symlink(), 'Refuse symlink write destination')
    need(item(src) == expected and 'sha256' in expected, 'Copy input changed: ' + str(src))
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    # O_EXCL temp prevents reuse; failure leaves evidence and is never retried.
    tmp = dst.with_name(dst.name + '.reviewed-r9-tmp')
    with Path(src).open('rb') as f, tmp.open('xb') as out:
        shutil.copyfileobj(f, out, 1024 * 1024)
        out.flush()
        os.fsync(out.fileno())
    need(item(tmp) == expected, 'Copied bytes mismatch')
    os.replace(tmp, dst)

def execute(plan, root, active=False, review=None):
    need(review is not None, 'Parent-authored r8 failure acceptance required')
    from cache_lineage import require_ready
    require_ready(plan)
    live = native_processes(plan)
    need(not live, 'LIVE_NATIVE_BUILD: ' + json.dumps(live))
    with acquire(plan) as lock:
        need(not native_processes(plan), 'Native build appeared after lock acquisition')
        revision_unused(plan)
        previous = terminal(plan, review)
        audit = audit_inputs(plan)
        lineage = require_ready(plan)  # Rebind selected native state under the original lock.
        need(Path(plan['clean_receipt']).is_file() and Path(plan['clean_receipt']).stat().st_size, 'Required prior clean receipt absent')
        if not active:
            return {'mode': 'PLAN_ONLY', 'eligible_at_check_time_only': True, 'audit': audit, 'native_lineage': lineage, 'build_started': False}
        attempt = Path(plan['run_root']) / 'attempt'
        attempt.mkdir()  # Exclusive one-shot claim; created only after all gates above.
        try:
            write(attempt / 'started.json', {'pid': os.getpid(), 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'prior': previous})
            preserve(plan, attempt, previous)
            # Recheck pinned inputs/preimages after potentially lengthy preservation.
            verify_pins(root)
            audit_inputs(plan)
            require_ready(plan)
            need(not native_processes(plan), 'Build appeared before integration')
            need(os.fstat(lock.fileno()).st_ino == Path(plan['lock']).stat().st_ino, 'Full-build lock inode changed')
            terminal(plan, review)
            apply(plan, attempt)
            record = Path(plan['logs']) / ('full-build-' + plan['revision'])
            with Path(str(record) + '.started').open('x') as f:
                f.write(datetime.datetime.now(datetime.timezone.utc).isoformat() + '\n')
            write(attempt / 'launch.json', {'revision': plan['revision'], 'lock_inode': os.fstat(lock.fileno()).st_ino, 'supervisor_pid': os.getpid()})
            env = os.environ.copy()
            for key in ['WITH_ADB_INSECURE', 'SELINUX_IGNORE_NEVERALLOWS', 'SOONG_ALLOW_MISSING_DEPENDENCIES', 'ALLOW_MISSING_DEPENDENCIES']:
                env.pop(key, None)
            env['REVIEWED_BUILD_LOCK_FD'] = str(lock.fileno())
            # Parent and child share the same flock open-file description. It is
            # held throughout integration, build and validation, including if the
            # Python supervisor is killed while the inherited child is running.
            with Path(str(record) + '.log').open('x') as log:
                child = subprocess.Popen(['bash', str(root / 'scripts/build.sh'), str(root)], env=env,
                                         pass_fds=(lock.fileno(),), stdout=log, stderr=subprocess.STDOUT)
                with Path(str(record) + '.pid').open('x') as f:
                    f.write(str(child.pid) + '\n')
                code = child.wait()
            Path(str(record) + '.exit-code').write_text(str(code) + '\n')
            if code == 0:
                validation = read(attempt / 'validation/complete.json')
                need(validation['flash_ready'] is False and validation['integration_receipt_sha256'] == sha(attempt / 'integration.json'), 'Successful child lacks bound host-validation evidence')
                Path(str(record) + '.complete').write_text(datetime.datetime.now(datetime.timezone.utc).isoformat() + '\n')
            Path(str(record) + '.finished').write_text(datetime.datetime.now(datetime.timezone.utc).isoformat() + '\n')
            need(code == 0, 'Build/validation failed; preserve attempt, no retry')
            write(attempt / 'complete.json', {'revision': plan['revision'], 'host_validation_completed': True, 'flash_ready': False})
            return {'mode': 'PARENT_EXECUTE', 'revision': plan['revision'], 'flash_ready': False}
        except BaseException as e:
            if not (attempt / 'FAILED.json').exists():
                write(attempt / 'FAILED.json', {'error': str(e), 'partial_state_preserved': True, 'retry_allowed': False})
            raise

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['PLAN_ONLY', 'PARENT_EXECUTE'], default='PLAN_ONLY')
    parser.add_argument('--describe-prior', action='store_true', help='Read terminal result under the real lock; emit an unapproved failure-review template')
    parser.add_argument('--prior-failure-review', type=Path, help='Parent-authored JSON under this kit parent-review directory')
    parser.add_argument('--prior-failure-review-sha256', help='Exact parent-reviewed JSON hash; required with the review file')
    parser.add_argument('--audit-inputs', action='store_true', help='Read-only inputs/preimages audit; never implies terminal eligibility')
    args = parser.parse_args()
    try:
        need(__debug__, 'Optimized Python forbidden')
        seal = verify_pins(ROOT)
        plan = read(ROOT / 'inputs/plan.json')
        need(str(ROOT) == plan['run_root'], 'Execute this pinned kit only from its reviewed builder directory')
        need(not ((args.audit_inputs or args.describe_prior) and args.mode != 'PLAN_ONLY'), 'Read-only actions cannot execute')
        need(not (args.audit_inputs and args.describe_prior), 'Select one read-only action')
        need(bool(args.prior_failure_review) == bool(args.prior_failure_review_sha256), 'Review file and exact SHA256 must be paired')
        review = (args.prior_failure_review, args.prior_failure_review_sha256) if args.prior_failure_review else None
        if args.describe_prior:
            need(not review, 'Describe does not accept prior approval')
            need(not native_processes(plan), 'LIVE_NATIVE_BUILD: cannot describe a terminal result')
            with acquire(plan):
                need(not native_processes(plan), 'Native build appeared after lock acquisition')
                result = terminal(plan, describe=True)
        else:
            if args.audit_inputs:
                from cache_lineage import require_ready
                result = {'scope': 'SELECTED_CURRENT_SOURCE_AND_EXPLICIT_61_OUTPUT_LINEAGE; complete baseline repeated at parent integration/final validation', 'source': audit_inputs(plan, baseline=False), 'lineage': require_ready(plan)}
            else:
                result = execute(plan, ROOT, args.mode == 'PARENT_EXECUTE', review)
        print(json.dumps({'kit_pins_sha256': seal, 'result': result}, indent=2))
    except (Refusal, OSError, ValueError, KeyError, subprocess.CalledProcessError) as e:
        print(json.dumps({'status': 'REFUSED', 'error': str(e), 'build_started_by_this_check': False if args.mode == 'PLAN_ONLY' else 'see preserved attempt'}, indent=2))
        return 20
    return 0

if __name__ == '__main__':
    sys.exit(main())
