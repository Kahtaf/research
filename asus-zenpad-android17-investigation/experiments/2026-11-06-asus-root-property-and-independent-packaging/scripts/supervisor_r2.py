"""Finite host-only run, retaining the original nonblocking lock and evidence."""
from pathlib import Path
import datetime
import json
import os
import resource
import signal
import subprocess
import sys
import time

ROOT = Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
OWN = Path('/srv/android/asus-r9-independent-packaging-r2')
sys.path.insert(0, str(ROOT / 'scripts'))
from integrate import need, sha, read, write, verify_pins, acquire, native_processes

def deadline(signum, frame):
    if 'child' in globals() and child.poll() is None:
        os.killpg(child.pid, signal.SIGKILL)
    raise TimeoutError('Whole supervisor reached finite 1190 second deadline')

signal.signal(signal.SIGALRM, deadline)
signal.signal(signal.SIGTERM, deadline)
signal.alarm(1190)

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def allocation():
    return sum(p.lstat().st_blocks * 512 for revision in (1, 2, 3) for p in Path('/srv/android/asus-r9-postbuild-validation-r' + str(revision)).rglob('*')) + sum(p.lstat().st_blocks * 512 for p in OWN.rglob('*')) + sum(p.lstat().st_blocks * 512 for p in Path('/srv/android/asus-r9-independent-packaging-r1').rglob('*'))

def preserved():
    plan = read(ROOT / 'inputs/plan.json')
    files = [p for p in (ROOT / 'attempt').rglob('*') if p.is_file()]
    files += [p for p in Path(plan['logs']).glob('full-build-r9.*') if p.is_file()]
    files += [p for p in Path('/srv/android/asus-r9-postbuild-validation-r1').rglob('*') if p.is_file()]
    files += [p for p in Path('/srv/android/asus-r9-postbuild-validation-r2').rglob('*') if p.is_file()]
    files += [p for p in Path('/srv/android/asus-r9-postbuild-validation-r3').rglob('*') if p.is_file()]
    files += [p for p in Path('/srv/android/asus-r9-independent-packaging-r1').rglob('*') if p.is_file()]
    return {str(p): {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(files)}

resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024**3, 4 * 1024**3))
cpus = sorted(os.sched_getaffinity(0))[:4]
os.sched_setaffinity(0, cpus)
os.environ.update(PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4')
plan = read(ROOT / 'inputs/plan.json')
need(Path(plan['lock']).stat().st_ino == 15018964, 'Wrong original lock inode')
lock = acquire(plan)
need(os.fstat(lock.fileno()).st_ino == 15018964, 'Lock changed during acquisition')
native_at_entry = native_processes(plan)
need(not native_at_entry, 'Native job active')
need(verify_pins(ROOT) == '744fa117bba0e4ba9895af792ddc71f1cbe99196cb752593e560064ef8d41e69', 'Wrong sealed kit')
record = Path(plan['logs']) / 'full-build-r9'
need(Path(str(record) + '.exit-code').read_text().strip() == '1' and Path(str(record) + '.finished').is_file(), 'Original R9 not terminal failed')
need(read(ROOT / 'attempt/FAILED.json')['retry_allowed'] is False, 'Missing consumed failure')
native = {phase: read(ROOT / 'attempt/native-evidence' / phase / 'receipt.json') for phase in ('host_init_verifier', 'bootimage')}
need(all(v['exit_code'] == 0 for v in native.values()), 'Native phase did not exit zero')
for phase, receipt in native.items():
    for name, pin in receipt['files'].items():
        p = ROOT / 'attempt/native-evidence' / phase / name
        need(p.stat().st_size == pin['bytes'] and sha(p) == pin['sha256'], 'Native evidence drift')
report = read(Path(str(record) + '.images.json'))
p = Path(plan['product_out'])
expected = {'boot': (9242624, '4b83266cc1f7f14a95d6e8ad5da490e1d358a4a1cebbdb2354454790a0d05b51'),
            'system': (2583003956, '827904b17c29df5f0f213d3b94adc4a24ea007c698eeb60c61092a524b380ff3')}
for name, (size, digest) in expected.items():
    path = p / (name + '.img')
    need(path.stat().st_size == size and sha(path) == digest == report[name]['sha256'], 'Original image drift: ' + name)
need(report['system']['expanded_bytes'] == 3753902080, 'Wrong expanded length')
lib = p / 'system/lib/liblog.so'
need(sha(lib) == '473bb94ce06678bffd72eb2c34d2f105d540cdedba6e5cc9c4f2c2d073449f9d' and lib.read_bytes()[:5] == b'\x7fELF\x01', 'Wrong actual ARM32 provider')
before = preserved()
write(OWN / 'preflight.json', {'utc': utc(), 'kit_seal': verify_pins(ROOT), 'original_overall_exit': 1,
      'native_phases': native, 'source_images': expected, 'original_evidence': before,
      'lock_inode': os.fstat(lock.fileno()).st_ino, 'native_processes': native_at_entry,
      'cpus': cpus, 'per_process_address_space_bytes': 4 * 1024**3,
      'owned_allocation_limit_bytes': 16 * 1024**3, 'supervisor_timeout_seconds': 1200,
      'hard_aggregate_resource_claim': False,
      'code_sha256': {str(x): sha(x) for x in (OWN / 'scripts').glob('*.py')}})
env = dict(os.environ, REVIEWED_BUILD_LOCK_FD=str(lock.fileno()))
started = time.monotonic()
peak = allocation()
reason = None
with (OWN / 'worker.log').open('xb') as log:
    child = subprocess.Popen([sys.executable, '-B', str(OWN / 'scripts/worker.py')],
                             stdout=log, stderr=subprocess.STDOUT, env=env,
                             cwd=OWN, pass_fds=(lock.fileno(),), start_new_session=True)
    write(OWN / 'started.json', {'utc': utc(), 'supervisor_pid': os.getpid(), 'worker_pid': child.pid})
    while child.poll() is None:
        peak = max(peak, allocation())
        if time.monotonic() - started > 1170:
            reason = 'supervisor deadline'
        if peak > 16 * 1024**3:
            reason = 'owned allocation limit'
        if reason:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=5)
            break
        time.sleep(1)
after = preserved()
need(before == after, 'Original attempt/log evidence changed')
need(verify_pins(ROOT) == '744fa117bba0e4ba9895af792ddc71f1cbe99196cb752593e560064ef8d41e69', 'Kit postcheck drift')
for name, (_, digest) in expected.items():
    need(sha(p / (name + '.img')) == digest, 'Source image postcheck drift')
result_path = OWN / 'checks/independent-results.json'
results = read(result_path) if result_path.is_file() else None
result = {'utc': utc(), 'worker_exit': child.returncode, 'stop_reason': reason,
          'elapsed_seconds': time.monotonic() - started, 'peak_observed_owned_allocation_bytes': peak,
          'original_and_prior_evidence_unchanged': True, 'original_r9_overall_exit': 1,
          'original_native_phase_exits': {k: v['exit_code'] for k, v in native.items()},
          'kit_pins_sha256': verify_pins(ROOT), 'worker_sha256': sha(OWN / 'scripts/worker.py'),
          'independent_results_sha256': sha(result_path) if results else None,
          'phase_results': {k: v['passed'] for k, v in results['phases'].items()} if results else None,
          'root_route_accepted': False, 'overall_validation_passed': False, 'flash_ready': False,
          'worker_log_sha256': sha(OWN / 'worker.log')}
write(OWN / 'outcome.json', result)
print(json.dumps(result), flush=True)
