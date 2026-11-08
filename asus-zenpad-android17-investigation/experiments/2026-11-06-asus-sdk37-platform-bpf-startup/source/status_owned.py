from pathlib import Path
import subprocess as s
O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106')
for p in (O/'evidence').glob('*.pid'):
 pid=p.read_text().strip();print('JOB',p.name,pid);print(s.run(['ps','-p',pid,'-o','pid,ppid,etime,stat,rss,vsz,args'],capture_output=True,text=True).stdout)
for p in [O/'evidence/build_owned.supervisor.log',O/'build/postimage/build.log',O/'evidence/build-result.json']:
 print('FILE',p);print(p.read_text()[-6000:] if p.exists() else 'NOT PRESENT')
print('PARENT JOB');print(s.run(['ps','-p','78673,132874','-o','pid,ppid,etime,stat,comm'],capture_output=True,text=True).stdout)
