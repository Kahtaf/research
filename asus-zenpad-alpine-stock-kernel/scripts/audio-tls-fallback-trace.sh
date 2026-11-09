set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
python3 - <<'PY'
from pathlib import Path
import json,signal,subprocess,time,urllib.request
assert not Path('/run/asus-goodix/rotation-trial/REQUEST').exists(), 'Finish landscape trial first'
folder=Path('/tmp/asus-media-trial')
assert not list(folder.glob('tls-trace.*')), 'Preserve the previous trace'
state=json.load(urllib.request.urlopen('http://127.0.0.1:8083/state',timeout=1))
assert Path('/proc',str(state['pid']),'cmdline').read_bytes().endswith(b'/tmp/asus-media-trial/media-fixture.py\0')
processes=[]
for process in Path('/proc').iterdir():
 if not process.name.isdecimal():continue
 try:args=(process/'cmdline').read_bytes().split(b'\0')
 except FileNotFoundError:continue
 if args and args[0]==b'/usr/lib/firefox-esr/firefox-esr':processes.append(process.name)
assert processes
owner=int(Path('/root/.mozilla/asus-appliance/lock').readlink().name.rsplit('+',1)[1])
windows=subprocess.check_output(['xdotool','search','--pid',str(owner),'--class','firefox'],text=True).split()
windows=[window for window in windows if '"Navigator"' in subprocess.check_output(['xprop','-id',window,'WM_CLASS'],text=True)]
assert len(windows)==1
assert 'ASUS media trial' in subprocess.check_output(['xdotool','getwindowname',windows[0]],text=True)
trace=['strace','-f','-ff','-e','trace=membarrier,tkill,tgkill,rt_sigprocmask','-e','signal=SIGSYS','-o',str(folder/'tls-trace')]
for pid in processes:trace+=['-p',pid]
with (folder/'tls-observer.log').open('wb') as output:
 tracer=subprocess.Popen(trace,stdout=output,stderr=subprocess.STDOUT)
 try:
  time.sleep(1);assert tracer.poll() is None
  subprocess.run(['xdotool','windowactivate','--sync',windows[0]],check=True)
  subprocess.run(['xdotool','key','ctrl+r'],check=True)
  time.sleep(17)
 finally:
  if tracer.poll() is None:tracer.send_signal(signal.SIGINT)
  tracer.wait(timeout=5)
matches=0
for file in sorted(folder.glob('tls-trace.*')):
 lines=file.read_text().splitlines()
 fatal=[i for i,line in enumerate(lines) if 'tkill(' in line and 'tgkill(' not in line]
 if not fatal:continue
 matches+=1;print('THREAD_TRACE',file.name)
 for i,line in enumerate(lines):
  if 'membarrier(' in line or 'tkill(' in line or 'tgkill(' in line or 'killed by SIGSYS' in line:print(line)
  elif 'rt_sigprocmask(' in line and any(0<j-i<5 for j in fatal):print(line)
print('THREAD_TRACES_WITH_TKILL',matches,'TRACER_DETACHED')
PY
