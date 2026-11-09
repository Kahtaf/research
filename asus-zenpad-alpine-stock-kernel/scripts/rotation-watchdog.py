#!/usr/bin/env python3
"""Bound the RAM-only CW session; restore native portrait unless accepted."""
from pathlib import Path
import json, os, signal, subprocess, time

run=Path('/run/asus-goodix/rotation-trial')
request=run/'REQUEST'
assert os.uname().release=='3.18.35'
assert Path('/etc/asus-alpine-ram-release').read_text().strip()=='asus-alpine-stock-kernel-v1'
assert Path('/etc/asus-goodix/native-touch').read_text()=='libinput-v1\n'
assert not Path('/etc/asus-goodix/rotation').exists(), 'Trial requires portrait baseline'
assert request.read_text()=='cw-v1\n'
assert not (run/'state.json').exists(), 'Refuse a stale trial'
deadline=time.monotonic()+180
ready=False
state={'pid':os.getpid(),'phase':'ARMED','deadline_monotonic':deadline}

def save():
    temporary=run/'state.json.new';temporary.write_text(json.dumps(state)+'\n');temporary.replace(run/'state.json')

def args(pid):
    try:return Path('/proc',str(pid),'cmdline').read_bytes().split(b'\0')
    except FileNotFoundError:return []

def stop(pid,original):
    if not original or args(pid)!=original:return
    os.kill(pid,signal.SIGTERM)
    for _ in range(150):
        if args(pid)!=original:return
        time.sleep(.1)
    raise RuntimeError('Owned process did not stop: '+str(pid))

save()
try:
    while time.monotonic()<deadline:
        if not ready and (run/'READY').exists():
            assert (run/'READY').read_text()=='landscape-browser-ready-v1\n'
            ready=True;deadline=time.monotonic()+360
            state.update(phase='READY_FOR_PHYSICAL',deadline_monotonic=deadline);save()
        if (run/'ACCEPTED').exists():
            assert ready, 'Cannot accept before browser readiness'
            assert (run/'ACCEPTED').read_text()=='landscape-physically-verified-v1\n'
            assert request.read_text()=='cw-v1\n'
            state['phase']='ACCEPTED_RAM_ONLY';save();raise SystemExit(0)
        time.sleep(.5)
except Exception as error:
    # Invalid readiness/acceptance receipts must return to portrait too.
    state['receipt_error']=str(error);save()

try:
    state['phase']='RESTORING_PORTRAIT';save()
    assert request.read_text()=='cw-v1\n'
    request.unlink();os.sync()
    env={**os.environ,'DISPLAY':':0','XAUTHORITY':'/run/asus-goodix/Xauthority'}
    for process in Path('/proc').iterdir():
        if not process.name.isdecimal():continue
        original=args(int(process.name))
        if original and original[0]==b'/usr/lib/firefox-esr/firefox-esr' and b'/root/.mozilla/asus-appliance' in original:
            windows=subprocess.run(['xdotool','search','--onlyvisible','--pid',process.name],env=env,capture_output=True,text=True).stdout.split()
            for window in windows:subprocess.run(['xdotool','windowclose',window],env=env,check=True)
            time.sleep(2);stop(int(process.name),original)
    pidfile=Path('/run/asus-goodix/desktop.pid')
    if pidfile.exists():
        pid=int(pidfile.read_text());original=args(pid)
        if any(b'asus-goodix-desktop' in value for value in original):stop(pid,original)
    for _ in range(50):
        if not Path('/tmp/.X11-unix/X0').exists():break
        time.sleep(.1)
    assert not Path('/tmp/.X11-unix/X0').exists(), 'X0 remains; inspect before restart'
    if pidfile.exists() and not args(int(pidfile.read_text())):pidfile.unlink()
    subprocess.run(['/etc/asus-alpine/start-desktop'],check=True,timeout=10)
    state['phase']='RESTORED_NATIVE_PORTRAIT';save()
except Exception as error:
    state.update(phase='ROLLBACK_NEEDS_INSPECTION',error=str(error));save();raise
