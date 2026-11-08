from pathlib import Path
import subprocess as s,json
O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106')
for p in sorted((O/'evidence').glob('run_owned-*.pid')):
 pid=p.read_text().strip();print('NATIVE_JOB',p.name,pid);print(s.run(['ps','-p',pid,'-o','pid,ppid,etime,stat,rss,vsz,comm'],capture_output=True,text=True).stdout)
for p in sorted(O.glob('run-*')):
 print('RUN',p.name)
 for name in ['result.json','host-resources.txt']:
  q=p/name
  if q.exists():print(name,q.read_text())
 q=p/'serial.log'
 if q.exists():print('SERIAL TAIL',q.read_text(errors='replace')[-15000:])
