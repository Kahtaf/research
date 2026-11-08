"""One-shot parent-authorized integration, selected native build and validation."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import time
import traceback

ROOT = Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
OWN = Path('/srv/android/asus-root-enabled-incremental-r1')
sys.path.insert(0, str(ROOT / 'scripts'))
from integrate import need, sha, read, write, manifest, verify_pins, verify_integrated, acquire, native_processes

START = time.monotonic()
child = None
def deadline(signum, frame):
    if child is not None and child.poll() is None:
        os.killpg(child.pid, signal.SIGKILL)
    raise TimeoutError('One-shot whole-attempt 1780 second deadline reached')
signal.signal(signal.SIGALRM, deadline)
signal.signal(signal.SIGTERM, deadline)
signal.alarm(1780)
resource.setrlimit(resource.RLIMIT_AS, (56 * 1024**3, 56 * 1024**3))
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
os.environ.update(PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0', OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4')

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def prior_files():
    files = [p for p in (ROOT / 'attempt').rglob('*') if p.is_file()]
    files += [p for p in Path('/srv/android/asus-device-product/logs').glob('full-build-r9.*') if p.is_file()]
    for prefix in [*(Path('/srv/android') / ('asus-r9-postbuild-validation-r' + str(n)) for n in (1, 2, 3)),
                   *(Path('/srv/android') / ('asus-r9-independent-packaging-r' + str(n)) for n in (1, 2))]:
        files += [p for p in prefix.rglob('*') if p.is_file()]
    return {str(p): {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(files)}

def allocated():
    return sum(p.lstat().st_blocks * 512 for p in OWN.rglob('*'))

peak = allocated()
def run_owned(argv, log_name, host=False):
    global child, peak
    env = dict(os.environ, REVIEWED_BUILD_LOCK_FD=str(lock.fileno()))
    def host_limit():
        resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
    log = OWN / 'logs' / log_name
    with log.open('xb') as stream:
        child = subprocess.Popen(list(map(str, argv)), stdout=stream, stderr=subprocess.STDOUT,
              env=env, cwd=OWN, pass_fds=(lock.fileno(),), start_new_session=True,
              preexec_fn=host_limit if host else None)
        write(OWN / 'attempt' / (log_name + '-started.json'), {'utc': utc(), 'pid': child.pid, 'argv': list(map(str, argv))})
        while child.poll() is None:
            peak = max(peak, allocated())
            if peak > 8 * 1024**3:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=5)
                raise RuntimeError('New owned allocation exceeded +8 GiB')
            time.sleep(1)
    code = child.returncode
    write(OWN / 'attempt' / (log_name + '-exit.json'), {'utc': utc(), 'exit': code, 'log': str(log), 'sha256': sha(log)})
    child = None
    return code

plan = read(ROOT / 'inputs/plan.json')
need(Path(plan['lock']).stat().st_ino == 15018964, 'Wrong existing lock inode')
lock = acquire(plan)
need(os.fstat(lock.fileno()).st_ino == 15018964, 'Lock inode changed during acquisition')
native_at_entry = native_processes(plan)
need(not native_at_entry, 'Active native engine; refuse without waiting')
need(not (OWN / 'attempt').exists(), 'Attempt already consumed; no retry')
(OWN / 'attempt').mkdir()
(OWN / 'logs').mkdir()
write(OWN / 'attempt/started.json', {'utc': utc(), 'supervisor_pid': os.getpid(), 'lock_inode': 15018964,
      'native_at_entry': native_at_entry, 'timeout_seconds': 1780, 'native_jobs': 4, 'retry_allowed': False})
try:
    acceptance = read(OWN / 'inputs/parent-acceptance.json')
    need(acceptance['parent_authorized_actual_execution'] is True, 'Parent execution acceptance missing')
    need(sha(OWN / 'inputs/source.patch') == acceptance['patch_sha256'] == 'babbe11017688a24aa64f3b279e0fa751e7e365608c77e6c65c164bb0890fb60', 'Wrong accepted patch')
    need(verify_pins(ROOT) == '744fa117bba0e4ba9895af792ddc71f1cbe99196cb752593e560064ef8d41e69', 'Sealed R9 kit changed')
    for relative, digest in read(OWN / 'inputs/owned-code-pins.json').items():
        need(sha(OWN / relative) == digest, 'Owned code/input drift: ' + relative)
    need(Path(plan['logs'], 'full-build-r9.exit-code').read_text().strip() == '1' and Path(plan['logs'], 'full-build-r9.finished').is_file(), 'Prior R9 is not terminal failed')
    need(read(ROOT / 'attempt/FAILED.json')['retry_allowed'] is False, 'Original failure missing')
    for phase in ('host_init_verifier', 'bootimage'):
        need(read(ROOT / 'attempt/native-evidence' / phase / 'receipt.json')['exit_code'] == 0, 'Prior actual native phase nonzero')
    for n in (1, 2, 3):
        need(read(Path('/srv/android') / ('asus-r9-postbuild-validation-r' + str(n)) / ('outcome-r' + str(n) + '.json'))['worker_exit'] == 1, 'Prior host failure changed')
    before = prior_files()
    write(OWN / 'attempt/preservation.json', {'files': before, 'old_raw_readonly': True})
    old_raw = Path('/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw')
    need(old_raw.stat().st_mode & 0o222 == 0 and sha(old_raw) == 'baa69560ace09a478c902077d8ff926d7a079ecb9b9f1632e4c330169b243798', 'Old raw image changed/not readonly')
    p = Path(plan['product_out'])
    need(sha(p / 'boot.img') == '4b83266cc1f7f14a95d6e8ad5da490e1d358a4a1cebbdb2354454790a0d05b51' and sha(p / 'system.img') == '827904b17c29df5f0f213d3b94adc4a24ea007c698eeb60c61092a524b380ff3', 'Prior native output images changed')
    source = Path(acceptance['source_path'])
    need(not source.is_symlink() and sha(source) == acceptance['preimage_sha256'], 'Active source preimage changed')
    need(sha(OWN / 'inputs/source-after.mk') == acceptance['postimage_sha256'], 'Staged source postimage changed')
    expected = read(plan['staged_receipt'])['product_after']
    need(manifest(plan['device']) == expected, 'Unrelated active product delta before integration')
    write(OWN / 'attempt/source-preflight.json', verify_integrated(plan, baseline=False))
    from cache_lineage import Session
    write(OWN / 'attempt/native-preflight.json', Session(ROOT, plan).preflight())
    for path, digest in plan['external_pins'].items():
        need(sha(path) == digest, 'Reviewed external input changed: ' + path)
    expected = dict(expected)
    expected['lineage_p00a.mk'] = {'sha256': acceptance['postimage_sha256']}
    write(OWN / 'inputs/expected-product.json', expected)
    scoped_plan = dict(plan, selected_incremental_log=str(OWN / 'logs/full-build-root-enabled-r1.log'))
    write(OWN / 'inputs/plan.json', scoped_plan)
    with (OWN / 'attempt/source-before.mk').open('xb') as stream:
        stream.write(source.read_bytes())
    write(OWN / 'attempt/parent-acceptance.json', {'instruction': acceptance,
          'acceptance_sha256': sha(OWN / 'inputs/parent-acceptance.json'),
          'original_kit_seal': verify_pins(ROOT), 'code_pins_sha256': sha(OWN / 'inputs/owned-code-pins.json'),
          'expected_product_sha256': sha(OWN / 'inputs/expected-product.json'), 'utc': utc()})
    need(not native_processes(plan), 'Native engine appeared before sole source write')
    need(sha(source) == acceptance['preimage_sha256'], 'Preimage changed immediately before write')
    with source.open('r+b') as stream:
        stream.write((OWN / 'inputs/source-after.mk').read_bytes())
        stream.truncate()
        stream.flush()
        os.fsync(stream.fileno())
    need(sha(source) == acceptance['postimage_sha256'] and manifest(plan['device']) == expected, 'Exact integrated product delta mismatch')
    integration = {'revision': 'root-enabled-incremental-r1', 'utc': utc(),
          'source_writes': [{'path': str(source), 'before': acceptance['preimage_sha256'], 'after': acceptance['postimage_sha256']}],
          'retained_r9_integration_sha256': sha(ROOT / 'attempt/integration.json'),
          'parent_acceptance_sha256': sha(OWN / 'attempt/parent-acceptance.json'),
          'generated_defconfig': read(ROOT / 'attempt/integration.json')['generated_defconfig'],
          'kernel_release': read(ROOT / 'attempt/integration.json')['kernel_release'],
          'expected_product_sha256': sha(OWN / 'inputs/expected-product.json'), 'retry_allowed': False}
    write(OWN / 'attempt/integration.json', integration)
    write(OWN / 'attempt/build-consumed.json', {'utc': utc(), 'targets': ['systemimage', 'bootimage'], 'jobs': 4})
    print(json.dumps({'status': 'SOURCE_INTEGRATED_NATIVE_LAUNCH', 'utc': utc(), 'source_postimage': sha(source)}), flush=True)
    build_code = run_owned(['/bin/bash', OWN / 'scripts/build.sh'], 'full-build-root-enabled-r1.log')
    write(OWN / 'attempt/native-terminal.json', {'exit': build_code, 'utc': utc(), 'retry_allowed': False})
    need(build_code == 0, 'Actual selected incremental build failed; preserve attempt, no retry')
    host_code = run_owned([sys.executable, '-B', OWN / 'scripts/postbuild.py'], 'host-validation.log', host=True)
    need(host_code == 0, 'Postbuild semantic checks failed; preserve actual logs')
    need(manifest(plan['device']) == expected, 'Active product drift after build/validation')
    need(prior_files() == before, 'Original/prior failed evidence or old image bytes changed')
    need(verify_pins(ROOT) == '744fa117bba0e4ba9895af792ddc71f1cbe99196cb752593e560064ef8d41e69', 'Original sealed kit changed')
    complete = read(OWN / 'validation/complete.json')
    need(complete['root_route_accepted'] is True and complete['compatibility_incomplete'] is True, 'Wrong final host scope')
    write(OWN / 'attempt/host-assembly-complete.json', {'utc': utc(), 'native_exit': 0, 'host_exit': 0,
          'root_route_accepted': True, 'compatibility_incomplete': True, 'overall_validation_passed': False,
          'complete_sha256': sha(OWN / 'validation/complete.json'), 'prior_evidence_unchanged': True,
          'peak_observed_owned_allocation_bytes': peak, 'elapsed_seconds': time.monotonic() - START,
          'physical_boot_verified': False, 'flash_ready': False})
    print((OWN / 'attempt/host-assembly-complete.json').read_text(), flush=True)
except BaseException as e:
    with (OWN / 'attempt/failure.log').open('x') as stream:
        traceback.print_exc(file=stream)
    result = {'utc': utc(), 'error': str(e), 'type': type(e).__name__, 'retry_allowed': False,
              'elapsed_seconds': time.monotonic() - START, 'peak_observed_owned_allocation_bytes': peak,
              'source_postimage': sha(Path('/srv/android/lineage24/device/asus/p00a/lineage_p00a.mk')),
              'original_r9_overall_exit': 1, 'overall_validation_passed': False, 'flash_ready': False}
    write(OWN / 'attempt/FAILED.json', result)
    print(json.dumps(result), flush=True)
    raise
