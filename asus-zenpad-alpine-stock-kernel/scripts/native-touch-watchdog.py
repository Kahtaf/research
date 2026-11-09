#!/usr/bin/env python3
"""Rollback the native input marker unless this bounded trial is accepted."""
from pathlib import Path
import json,os,signal,subprocess,time
run=Path('/run/asus-goodix/native-trial');marker=Path('/etc/asus-goodix/native-touch')
deadline=time.monotonic()+180
ready=False
state={'pid':os.getpid(),'phase':'ARMED','deadline_monotonic':deadline}
def save():
 temp=run/'state.json.new';temp.write_text(json.dumps(state)+'\n');temp.replace(run/'state.json')
def args(pid):
 try:return Path('/proc',str(pid),'cmdline').read_bytes().split(b'\0')
 except FileNotFoundError:return []
def stop(pid,original):
 if args(pid)!=original:return
 os.kill(pid,signal.SIGTERM)
 for i in range(150):
  if args(pid)!=original:return
  time.sleep(.1)
 raise RuntimeError('Owned process did not stop; no forced kill: '+str(pid))
save()
while time.monotonic()<deadline:
 if not ready and (run/'READY').exists():
  assert (run/'READY').read_text()=='native-browser-ready-v1\n'
  ready=True;deadline=time.monotonic()+360
  state.update(phase='READY_FOR_PHYSICAL',deadline_monotonic=deadline);save()
 if (run/'ACCEPTED').exists():
  assert (run/'ACCEPTED').read_text()=='native-touch-verified-v1\n'
  assert marker.read_text()=='libinput-v1\n'
  state['phase']='ACCEPTED';save();raise SystemExit(0)
 time.sleep(.5)
try:
 if not marker.exists():state['phase']='EXPIRED_NO_NATIVE_MARKER';save();raise SystemExit(0)
 assert marker.read_text()=='libinput-v1\n'
 state['phase']='ROLLING_BACK';save();marker.unlink();os.sync()
 env={**os.environ,'DISPLAY':':0','XAUTHORITY':'/run/asus-goodix/Xauthority'}
 for p in Path('/proc').iterdir():
  if not p.name.isdecimal():continue
  a=args(int(p.name))
  if a and a[0]==b'/usr/lib/firefox-esr/firefox-esr' and b'/root/.mozilla/asus-appliance' in a:
   windows=subprocess.run(['xdotool','search','--onlyvisible','--pid',p.name],env=env,capture_output=True,text=True).stdout.split()
   for w in windows:subprocess.run(['xdotool','windowclose',w],env=env,check=True)
   time.sleep(2);stop(int(p.name),a)
 pidfile=Path('/run/asus-goodix/desktop.pid')
 if pidfile.exists():
  pid=int(pidfile.read_text());a=args(pid)
  if any(b'asus-goodix-desktop' in v for v in a):stop(pid,a)
 for i in range(50):
  if not Path('/tmp/.X11-unix/X0').exists():break
  time.sleep(.1)
 assert not Path('/tmp/.X11-unix/X0').exists(),'X0 remains; inspect before restarting'
 if pidfile.exists() and not args(int(pidfile.read_text())):pidfile.unlink()
 subprocess.run(['/etc/asus-alpine/start-desktop'],check=True,timeout=10)
 state['phase']='ROLLED_BACK_TO_POINTER_BRIDGE';save()
except Exception as error:
 state.update(phase='ROLLBACK_NEEDS_INSPECTION',error=str(error));save();raise
