"""Host-only completion after exact receipt/target-order corrections; no build."""
from pathlib import Path
import datetime
import os
import resource
import signal
import subprocess
import sys
import time
import traceback

ROOT = Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
OWN = Path('/srv/android/asus-root-enabled-incremental-r1')
HOST = OWN / 'host-r2'
sys.path.insert(0, str(ROOT / 'scripts'))
from integrate import read, write, sha, need, acquire, native_processes, manifest, verify_pins
resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['GIT_OPTIONAL_LOCKS'] = '0'
started = datetime.datetime.fromisoformat(read(OWN / 'attempt/started.json')['utc'])
remaining = int((started + datetime.timedelta(seconds=1780) - datetime.datetime.now(datetime.timezone.utc)).total_seconds())
need(remaining > 30, 'Original whole-work deadline exhausted')
child = None
def deadline(signum, frame):
    if child is not None and child.poll() is None:
        os.killpg(child.pid, signal.SIGKILL)
    raise TimeoutError('Original whole-work 1780-second deadline')
signal.signal(signal.SIGALRM, deadline)
signal.signal(signal.SIGTERM, deadline)
signal.alarm(remaining)
plan = read(OWN / 'inputs/plan.json')
lock = acquire(plan)
need(os.fstat(lock.fileno()).st_ino == 15018964 and not native_processes(plan), 'Lock/active native engine')
need(not (HOST / 'started.json').exists(), 'Host revision consumed; no repeat')
need(read(OWN / 'attempt/native-terminal.json')['exit'] == 0, 'Native build did not succeed')
need(read(OWN / 'attempt/native-evidence/selected-images/receipt.json')['exit_code'] == 0, 'Actual native phase nonzero')
need(sha(Path(plan['device']) / 'lineage_p00a.mk') == '9eef1d1e5463f43500863604641f8fb3af8d91fb9100b83f231b216041f79c75', 'Source postimage drift')
need(manifest(plan['device']) == read(OWN / 'inputs/expected-product.json'), 'Other active product input drift')
need(verify_pins(ROOT) == '744fa117bba0e4ba9895af792ddc71f1cbe99196cb752593e560064ef8d41e69', 'Original kit drift')
pins = read(HOST / 'inputs/code-pins.json')
for rel, digest in pins.items():
    need(sha(HOST / rel) == digest, 'Host revision source drift')
def protected():
    prior = read(OWN / 'attempt/preservation.json')['files']
    files = {str(p): {'bytes': p.stat().st_size, 'sha256': sha(p)}
             for folder in (OWN / 'attempt', OWN / 'logs') for p in folder.rglob('*') if p.is_file()}
    for name, row in prior.items():
        p = Path(name)
        need(p.stat().st_size == row['bytes'] and sha(p) == row['sha256'], 'Original/prior failure or old raw changed: ' + name)
    return files
before = protected()
write(HOST / 'started.json', {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'lock_inode': 15018964, 'native_reexecution': False, 'prior_failed_host_record_preserved': True,
      'remaining_whole_task_seconds': remaining, 'code_pins_sha256': sha(HOST / 'inputs/code-pins.json')})
peak = 0
try:
    env = dict(os.environ, REVIEWED_BUILD_LOCK_FD=str(lock.fileno()))
    with (HOST / 'host-validation.log').open('xb') as stream:
        child = subprocess.Popen([sys.executable, '-B', str(HOST / 'scripts/postbuild.py')],
             stdout=stream, stderr=subprocess.STDOUT, env=env, pass_fds=(lock.fileno(),), start_new_session=True)
        while child.poll() is None:
            peak = max(peak, sum(p.lstat().st_blocks * 512 for p in OWN.rglob('*')))
            if peak > 8 * 1024**3:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=5)
                raise RuntimeError('+8 GiB owned allocation exceeded')
            time.sleep(1)
    need(child.returncode == 0, 'Host semantic continuation failed; preserve log')
    need(protected() == before, 'Native/prior failed host files changed')
    complete = read(HOST / 'validation/complete.json')
    need(complete['root_route_accepted'] is True and complete['compatibility_incomplete'] is True, 'Wrong scoped completion')
    write(HOST / 'complete.json', {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'native_exit': 0, 'host_exit': 0, 'root_route_accepted': True, 'compatibility_incomplete': True,
          'overall_validation_passed': False, 'original_and_prior_evidence_unchanged': True,
          'first_host_failure_preserved': True, 'native_reexecution': False,
          'peak_observed_owned_allocation_bytes': peak, 'validation_complete_sha256': sha(HOST / 'validation/complete.json'),
          'code_pins_sha256': sha(HOST / 'inputs/code-pins.json'), 'flash_ready': False})
    print((HOST / 'complete.json').read_text(), flush=True)
except BaseException as e:
    with (HOST / 'failure.log').open('x') as stream:
        traceback.print_exc(file=stream)
    write(HOST / 'FAILED.json', {'error': str(e), 'type': type(e).__name__, 'retry_allowed': False,
          'native_exit': 0, 'overall_validation_passed': False, 'flash_ready': False})
    raise
