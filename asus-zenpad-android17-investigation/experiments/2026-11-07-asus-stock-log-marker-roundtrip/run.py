from pathlib import Path
import datetime, fcntl, hashlib, importlib.util, json, os, subprocess, sys, time, uuid

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
ADB = '/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools/adb'
SERIAL = 'DEVICE_SERIAL_REDACTED'
HELPER = WORK/'2026-11-07-asus-usb-retained-log-collector/scripts/root_shell_usb.py'
assert hashlib.sha256(HELPER.read_bytes()).hexdigest() == '76b28970223c63b9cdd6774c2190051953beee2d89cde1a22b30d1eebba5c78c'
assert not (ROOT/'evidence/run.json').exists(), 'One-shot experiment already attempted'
sys.path.insert(0, str(WORK/'2026-11-07-asus-linux49-failure-log-trial'))
spec = importlib.util.spec_from_file_location('prior_trial', WORK/'2026-11-07-asus-linux49-failure-log-trial/run_trial.py')
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
ENV = {k:v for k,v in os.environ.items() if not k.startswith(('ADB_', 'ANDROID_ADB_')) and k != 'ANDROID_SERIAL'}
ENV['PATH'] = str(WORK/'2026-11-07-asus-usb-retained-log-collector/scripts/usb-adb')+os.pathsep+ENV.get('PATH', '/usr/bin:/bin')
os.umask(0o077)
run = str(uuid.uuid4())
marker = 'ASUS_STOCK_CHANNEL_'+run
state = dict(run_id=run, marker=marker, status='PREPARING', utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
             normal_OS_partition_writes=False, firmware_flash=False, VM_start=False,
             operation='one stock log write and one normal reboot', early49_checkpoint_proven=False)
save = lambda: prior.save(ROOT/'evidence/run.json', state)
save()
lockpath = WORK/'2026-11-06-asus-recovery-control-transport/evidence/execute.lock'
with lockpath.open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    before = prior.query(SERIAL)
    assert before, 'Verified stock identity required'
    state['previous_boot_id'] = before
    body = '''
[ "$(cat /proc/sys/kernel/random/boot_id)" = "BOOT_PIN" ]
[ "$(uname -r)" = 3.18.35 ]
[ -c /dev/kmsg ]
[ ! -L /dev/kmsg ]
[ "$(stat -c '%t:%T' /dev/kmsg)" = 1:b ]
[ -f /proc/last_kmsg ]
[ ! -L /proc/last_kmsg ]
/system/bin/toybox grep -E '^ram-1[[:space:]].*[(]E' /proc/consoles
read current default minimum boot < /proc/sys/kernel/printk
[ "$current" -ge 1 ]
printf '<0>MARKER stage=stock_console_calibration\\n' > /dev/kmsg
dmesg | /system/bin/toybox grep -F 'MARKER'
[ "$(cat /proc/sys/kernel/random/boot_id)" = "BOOT_PIN" ]
printf 'PRE_REBOOT_MARKER_CONFIRMED\\n'
'''.replace('BOOT_PIN', before).replace('MARKER', marker)
    # Literal substitutions affect marker text only; do not accept command syntax.
    assert all(c.isalnum() or c in '_-' for c in marker)
    state['marker_write_may_dispatch'] = True
    save()
    q = subprocess.run(['python3', '-B', str(HELPER)], input=body.encode(),
                       env=ENV, capture_output=True, timeout=90)
    (ROOT/'private/marker-helper.stdout').write_bytes(q.stdout)
    (ROOT/'private/marker-helper.stderr').write_bytes(q.stderr)
    state['helper_exit'] = q.returncode
    # Replacement intentionally changed the fixed completion token too.
    confirmed = ('PRE_REBOOT_'+marker+'_CONFIRMED').encode()
    assert q.returncode == 0 and confirmed in q.stdout and (marker+' stage=stock_console_calibration').encode() in q.stdout, 'Marker confirmation failed: no reboot'
    state.update(pre_reboot_kernel_ring_marker_verified=True, enforcing_restored=True, status='MARKER_CONFIRMED')
    save()
    assert prior.query(SERIAL) == before, 'Stock boot changed before reboot'
    state.update(reboot_requests=1, reboot_kind='NORMAL', dispatch='DISPATCHING')
    save()
    try:
        q = subprocess.run([ADB, '-s', SERIAL, 'reboot'], env=ENV,
                           capture_output=True, text=True, timeout=12)
        state.update(dispatch='ACKNOWLEDGED' if q.returncode == 0 else 'UNKNOWN', reboot_command_exit=q.returncode)
    except (subprocess.TimeoutExpired, UnicodeError) as e:
        state.update(dispatch='UNKNOWN', dispatch_error=type(e).__name__)
    save()
print(json.dumps({'marker':marker,'dispatch':state['dispatch'],'previous_boot_id':before}), flush=True)
deadline = time.monotonic()+240
while time.monotonic() < deadline:
    try:
        current = prior.query(SERIAL)
    except (subprocess.TimeoutExpired, UnicodeError, ValueError):
        current = None
    if current and current != before:
        state.update(status='STOCK_RETURN_VERIFIED', new_stock_boot_id=current,
                     observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        save()
        # Existing bounded collector requires the actual recovery pin even for a normal reboot.
        receipt = dict(dispatch=state['dispatch'], previous_boot_id=before,
                       candidate_p10_sha256='0b1a3c45751d688ba304743dc74e73f7030586c6fafece32eedf0da39c86455d',
                       recovery_unchanged=True, reboot_kind='NORMAL', normal_OS_writes=False)
        prior.save(ROOT/'evidence/normal-reboot-entry.json', receipt)
        print(json.dumps({'outcome':'verified_stock_return','boot_id':current,'marker':marker}), flush=True)
        raise SystemExit(0)
    time.sleep(3)
state.update(status='NO_VERIFIED_RETURN_AT_DEADLINE')
save()
print(json.dumps({'outcome':state['status'],'no_reboot_retry':True}), flush=True)
raise SystemExit(2)
