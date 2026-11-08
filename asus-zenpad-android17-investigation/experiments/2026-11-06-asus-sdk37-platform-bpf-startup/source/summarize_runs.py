from pathlib import Path
import json,re,subprocess as s
O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106')
for p in sorted((O/'evidence').glob('run_owned*.pid')):
 pid=p.read_text().strip();print('JOB',p.name,pid,s.run(['ps','-p',pid,'-o','stat=,comm='],capture_output=True,text=True).stdout.strip())
for r in sorted(O.glob('run-*')):
 print('RUN',r.name)
 if (r/'result.json').exists():print((r/'result.json').read_text())
 if (r/'serial.log').exists():
  lines=(r/'serial.log').read_text(errors='replace').splitlines()
  for l in lines:
   if any(x in l for x in ['EXEC_RESULT','WHOLE_LOADER','ACTUAL_UNAME','Error when loading','below its kernel minimum','PLATFORM_FIXTURE_','panicked','CRITICAL FAILURE','Failed to create maps','Skipping load','Loading /system','Loading legacy','transferring control','Failed to set bpf.progs_loaded']):print(l)
  print('TAIL','\n'.join(lines[-5:]))
