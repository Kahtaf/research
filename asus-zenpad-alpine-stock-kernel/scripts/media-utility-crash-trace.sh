set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
python3 - <<'PY'
from pathlib import Path
import os, signal, subprocess, time
processes=[]
for p in Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try:a=(p/'cmdline').read_bytes().split(b'\0')
 except FileNotFoundError:continue
 if a and a[0]==b'/usr/lib/firefox-esr/firefox-esr':processes.append(p.name)
assert processes
trace=['strace','-f','-ff','-e','trace=none','-e','signal=SIGSYS,SIGSEGV,SIGABRT,SIGILL','-o','/tmp/asus-media-trial/signals']
for pid in processes:trace+=['-p',pid]
with Path('/tmp/asus-media-trial/strace.log').open('wb') as log:
 tracer=subprocess.Popen(trace,stdout=log,stderr=subprocess.STDOUT)
 try:
  time.sleep(1)
  assert tracer.poll() is None
  owner=int(Path('/root/.mozilla/asus-appliance/lock').readlink().name.rsplit('+',1)[1])
  windows=subprocess.check_output(['xdotool','search','--pid',str(owner),'--class','firefox'],text=True).split()
  windows=[w for w in windows if '"Navigator"' in subprocess.check_output(['xprop','-id',w,'WM_CLASS'],text=True)]
  assert len(windows)==1
  subprocess.run(['xdotool','windowactivate','--sync',windows[0]],check=True)
  subprocess.run(['xdotool','key','ctrl+r'],check=True)
  time.sleep(17)
 finally:
  if tracer.poll() is None:tracer.send_signal(signal.SIGINT)
  tracer.wait(timeout=5)
for p in sorted(Path('/tmp/asus-media-trial').glob('signals.*')):
 s=p.read_text()
 if any(x in s for x in ('SIGSYS','SIGSEGV','SIGABRT','SIGILL')):print(p.name,s)
print('TRACER_DETACHED')
PY
