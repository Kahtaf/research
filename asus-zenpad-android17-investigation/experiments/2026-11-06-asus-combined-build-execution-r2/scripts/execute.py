"""Direct parent-authorized combined build; no preparation-only admission layer."""
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

OWN = Path('/srv/android/asus-combined-build-execution-r2')
KIT = Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
sys.path.insert(0, str(KIT / 'scripts'))
from integrate import read, write, sha, need, acquire, native_processes, manifest
plan = read(OWN / 'inputs/base-plan.json')
start = time.monotonic()
child = None
def deadline(signum, frame):
    if child is not None and child.poll() is None:
        os.killpg(child.pid, signal.SIGKILL)
    raise TimeoutError('45-minute owned execution deadline')
signal.signal(signal.SIGALRM, deadline)
signal.alarm(2690)
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
os.environ.update(PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0', OMP_NUM_THREADS='4')
lock = acquire(plan)
need(os.fstat(lock.fileno()).st_ino == 15018964, 'Wrong original lock')
need(not native_processes(plan), 'Active native engine; no waiting or other-worker signalling')
need(not (OWN / 'attempt').exists(), 'Consumed native attempt; no repeat')
(OWN / 'attempt').mkdir(); (OWN / 'logs').mkdir()
native_limits = resource.getrlimit(resource.RLIMIT_AS)
write(OWN / 'attempt/native-address-space.json', {'soft': native_limits[0], 'hard': native_limits[1], 'unlimited_value': resource.RLIM_INFINITY, 'inherited_from_fresh_ssh': True, 'native_limits_changed_by_driver': False})
need(native_limits == (resource.RLIM_INFINITY, resource.RLIM_INFINITY), 'Fresh SSH native soft/hard RLIMIT_AS are not unlimited; refuse native launch')
write(OWN / 'attempt/started.json', {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'lock_inode': 15018964, 'native_jobs': 4, 'finite_deadline_seconds': 2690,
      'authorization': 'Parent message explicitly authorizes actual combined build now; no affirmative worker-as-parent acceptance fabricated'})
env = dict(os.environ, REVIEWED_BUILD_LOCK_FD=str(lock.fileno()))
def run(argv, filename, host=False):
    global child
    def small_host(): resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
    with (OWN / 'logs' / filename).open('xb') as log:
        child = subprocess.Popen(list(map(str, argv)), stdout=log, stderr=subprocess.STDOUT, env=env,
              cwd=OWN, pass_fds=(lock.fileno(),), start_new_session=True, preexec_fn=small_host if host else None)
        code = child.wait(timeout=max(1, 2680 - (time.monotonic() - start)))
    child = None
    return code
try:
    for local, remote in [('profile.json', '/srv/android/asus-device-profile-integration-20261106/journal.json'),
                          ('namespace.json', '/srv/android/asus-namespace-source-integration-20261106/journal.json')]:
        receipt = read(OWN / 'inputs' / local)
        need(receipt == read(remote) and receipt['status'] == 'SOURCE_INTEGRATED_NATIVE_BUILD_PENDING'
             and receipt['all_postimages_verified'] is True, 'Integrated receipt differs: ' + local)
        for row in receipt['changes']:
            need(sha(Path(plan['aosp']) / row['path']) == row['after_sha256'], 'Integrated postimage changed: ' + row['path'])
    need(manifest(plan['device']) == read(OWN / 'inputs/expected-product.json'), 'Unexpected product-source delta')
    kernel = Path(plan['device']) / 'prebuilt/Image.gz-dtb'
    need(sha(kernel) == 'e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1', 'Kernel prebuilt changed')
    need(sha(plan['defconfig']) == '10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2', 'Kernel config changed')
    old_raw = []
    for path in ['/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw',
                 '/srv/android/asus-root-enabled-incremental-r1/host-r2/validation/system-partition.raw']:
        p = Path(path); st = p.stat()
        need(st.st_mode & 0o222 == 0, 'Old raw must stay readonly')
        old_raw.append({'path': path, 'bytes': st.st_size, 'inode': st.st_ino, 'mtime_ns': st.st_mtime_ns, 'mode': st.st_mode})
    write(OWN / 'attempt/old-raw-stat-pins.json', old_raw)
    source = Path(plan['aosp']) / 'hardware/interfaces/health/utils/libhealthloop/filterPowerSupplyEvents.c'
    need(sha(source) == '71566db1d1609edded3261b5557fe1f62eea7f5387264105c8ddbec0a8f9ab84', 'Already integrated health source changed')
    write(OWN / 'inputs/plan.json', plan)
    prior = Path('/srv/android/asus-combined-build-execution-r1')
    prior_pins = {name: sha(prior / name) for name in ['logs/native.log', 'attempt/native-terminal.json', 'attempt/FAILED.json']}
    write(OWN / 'attempt/preserved-r1.json', prior_pins)
    write(OWN / 'attempt/integration.json', {'source_writes': [],
          'health_source_sha256': sha(source), 'already_integrated_health_retained': True,
          'profile_journal_sha256': sha(OWN / 'inputs/profile.json'),
          'namespace_journal_sha256': sha(OWN / 'inputs/namespace.json'), 'isolated_elf_installed': False})
    write(OWN / 'attempt/native-consumed.json', {'command': ['m', '-j4', 'systemimage', 'bootimage'],
          'lunch': 'lineage_p00a-trunk_staging-userdebug', 'once': True})
    print('Fresh SSH native RLIMIT_AS unlimited; integrated sources retained; actual combined build starting', flush=True)
    code = run(['/bin/bash', OWN / 'scripts/build.sh'], 'native.log')
    phase = OWN / 'attempt/native-evidence/selected-images/receipt.json'
    native_code = read(phase)['exit_code'] if phase.exists() else code
    write(OWN / 'attempt/native-terminal.json', {'exit': native_code, 'wrapper_exit': code,
          'elapsed_seconds': time.monotonic() - start, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    print(json.dumps({'actual_native_exit': native_code, 'wrapper_exit': code}), flush=True)
    need(native_code == 0 and code == 0, 'Actual native/compiler failure; preserve logs, no repeat')
    host_code = run([sys.executable, '-B', OWN / 'scripts/postbuild.py'], 'postbuild-r1.log', host=True)
    need(host_code == 0, 'Critical postbuild check failed; preserve outputs and exact log')
    for row in old_raw:
        st = Path(row['path']).stat()
        need((st.st_size, st.st_ino, st.st_mtime_ns, st.st_mode) ==
             (row['bytes'], row['inode'], row['mtime_ns'], row['mode']), 'Preserved old raw metadata changed')
    need(all(sha(prior / name) == value for name, value in prior_pins.items()), 'Failed r1 receipt/log changed')
    write(OWN / 'attempt/complete.json', {'native_exit': native_code, 'critical_postbuild_exit': host_code,
          'elapsed_seconds': time.monotonic() - start, 'old_raw_preserved_without_rehash': True,
          'receipt_sha256': sha(OWN / 'critical-checks.json'), 'device_accessed': False, 'flash_go': False})
    print((OWN / 'attempt/complete.json').read_text(), flush=True)
except BaseException as e:
    if child is not None and child.poll() is None:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=5)
    with (OWN / 'attempt/failure.log').open('x') as f: traceback.print_exc(file=f)
    write(OWN / 'attempt/FAILED.json', {'error': str(e), 'type': type(e).__name__,
          'elapsed_seconds': time.monotonic() - start, 'native_repeat_allowed': False, 'flash_go': False})
    raise
