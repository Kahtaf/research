"""Future combined attempt. Missing namespace/acceptance refuses before VM access."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
from admission import require_binding, read, sha, need, check_source_map

HOME = Path(__file__).resolve().parents[1]
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--host-revision')
    args = parser.parse_args()
    binding = require_binding(HOME)  # No process/source/out reads before this gate.
    for relative, expected_hash in read(HOME / 'inputs/owned-code-pins.json').items():
        need(sha(HOME / relative) == expected_hash, 'Prepared code/input pin changed')
    if not args.execute and not args.host_revision:
        print(json.dumps({'admission': 'BOUND', 'execution_started': False}))
        return
    import fcntl, datetime, resource, signal, time
    resource.setrlimit(resource.RLIMIT_AS, (56 * 1024**3, 56 * 1024**3))
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    deadline = time.monotonic() + 1780
    def run_child(argv, stream, env, fd, host=False):
        def limit_host(): resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
        child = subprocess.Popen(argv, env=env, stdout=stream, stderr=subprocess.STDOUT,
                  pass_fds=(fd,), start_new_session=True, preexec_fn=limit_host if host else None)
        try: return child.wait(timeout=max(1, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=5)
            raise ValueError('Bound selected attempt reached its finite deadline')

    root = Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
    sys.path.insert(0, str(root / 'scripts'))
    from integrate import acquire, native_processes, manifest, write, verify_pins, sha as streaming_sha
    plan = read(HOME / 'inputs/base-plan.json')
    lock = acquire(plan)
    need(os.fstat(lock.fileno()).st_ino == 15018964 and not native_processes(plan), 'Original lock/active native engine')
    need(verify_pins(root) == '744fa117bba0e4ba9895af792ddc71f1cbe99196cb752593e560064ef8d41e69', 'Original cohort changed')
    preserved_raw = {
        '/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw': 'baa69560ace09a478c902077d8ff926d7a079ecb9b9f1632e4c330169b243798',
        '/srv/android/asus-root-enabled-incremental-r1/host-r2/validation/system-partition.raw': '04b4d81f486ce4a17609300c3f6d2f92cecc1938ee0f0e64019a29bd8c870785'}
    for path, expected_hash in preserved_raw.items():
        need(Path(path).stat().st_mode & 0o222 == 0 and streaming_sha(path) == expected_hash, 'Preserved raw SYSTEM changed')
    expected = binding['expected_product']
    source_root = Path(plan['aosp'])
    env = dict(os.environ, REVIEWED_BUILD_LOCK_FD=str(lock.fileno()), PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0')
    if args.execute:
        need(not (HOME / 'attempt').exists(), 'Native attempt already consumed; use explicit host revisions only')
        (HOME / 'attempt').mkdir(); (HOME / 'logs').mkdir()
        write(HOME / 'attempt/started.json', {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'lock_inode': 15018964,
              'binding_sha256': sha(HOME / 'binding.json'), 'namespace_owner': 'e90477dc'})
        check_source_map(manifest(plan['device']), read(HOME / 'inputs/expected-profile-product.json'))
        writes = []
        for row in binding['namespace']['changes']:
            target = source_root / row['path']
            need(not target.is_symlink() and sha(target) == row['before_sha256'], 'Namespace active preimage mismatch')
            payload = Path(binding['namespace_handoff']).parent / row['payload_file']
            need(sha(payload) == row['after_sha256'], 'Namespace payload changed')
            backup = HOME / 'attempt/preimages' / row['path']; backup.parent.mkdir(parents=True, exist_ok=True)
            with backup.open('xb') as f: f.write(target.read_bytes())
            writes.append(row)
        # All preimages checked before the authorized namespace delta is written.
        for row in writes:
            target = source_root / row['path']; payload = Path(binding['namespace_handoff']).parent / row['payload_file']
            with target.open('r+b') as f: f.write(payload.read_bytes()); f.truncate(); f.flush(); os.fsync(f.fileno())
            need(sha(target) == row['after_sha256'], 'Namespace postimage mismatch')
        check_source_map(manifest(plan['device']), expected)
        write(HOME / 'inputs/expected-product.json', expected)
        plan['selected_incremental_log'] = str(HOME / 'logs/full-build-combined-r1.log')
        write(HOME / 'inputs/plan.json', plan)
        write(HOME / 'attempt/integration.json', {'source_writes': writes, 'already_integrated_profile': read(HOME / 'inputs/profile-journal.json'),
              'binding_sha256': sha(HOME / 'binding.json'), 'root_mk_unchanged': True})
        with (HOME / 'logs/full-build-combined-r1.log').open('xb') as f:
            code = run_child(['/bin/bash', str(HOME / 'scripts/build.sh')], f, env, lock.fileno())
        write(HOME / 'attempt/native-terminal.json', {'exit': code, 'native_reexecution_allowed': False})
        need(code == 0, 'Native attempt failed; preserve logs, no native repeat')
        # Actual source/config and namespace proof must remain exact after the build.
        from config_receipt import prepare_config_receipt
        prepare_config_receipt(HOME, binding)
    else:
        need(read(HOME / 'attempt/native-terminal.json')['exit'] == 0, 'Host validation requires genuine native success')
        check_source_map(manifest(plan['device']), expected)
    revision = args.host_revision or 'r1'
    need(revision.replace('-', '').isalnum(), 'Unsafe host revision')
    host = HOME / 'host' / revision
    host.mkdir(parents=True, exist_ok=False)
    env.update(HOST_REVISION_DIR=str(host), VALIDATION_DIR=str(host / 'validation'))
    with (host / 'validation.log').open('xb') as f:
        code = run_child([sys.executable, '-B', str(HOME / 'scripts/postbuild.py')], f, env, lock.fileno(), host=True)
    write(host / 'outcome.json', {'exit': code, 'native_rerun': False, 'log_sha256': sha(host / 'validation.log')})
    need(code == 0, 'Host checks failed; preserve log and use a new explicit host revision without native rerun')
if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError) as e:
        print(json.dumps({'status': 'REFUSED', 'reason': str(e), 'authorization_inferred': False}))
        raise SystemExit(20)
