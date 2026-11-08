from pathlib import Path
import os,subprocess,time,datetime,json
from vm import R,SSH,identity,run
os.chdir(R);identity('RUNNING','readiness-running')
assert not (R/'evidence/dispatch-local.json').exists()
for n in range(2,10):
 with (R/f'evidence/master-{n}.stdout').open('w') as out,(R/f'evidence/master-{n}.stderr').open('w') as err:
  p=subprocess.Popen(SSH[:-1]+['-M','-S','s','-o','ControlPersist=yes','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=12','-f','-N',SSH[-1]],stdout=out,stderr=err)
  try:code=p.wait(timeout=25)
  except subprocess.TimeoutExpired:
   p.kill();p.wait();code=124
 with (R/'evidence/lifecycle.jsonl').open('a') as f:f.write(json.dumps(dict(phase='master-'+str(n),exit=code,at=datetime.datetime.now(datetime.timezone.utc).isoformat()))+'\n')
 if (R/'s').is_socket():
  q=run(SSH[:-1]+['-S','s','-O','check',SSH[-1]],'master-ready',10)
  if q.returncode==0:print('Authenticated owned master ready',flush=True);break
 time.sleep(5)
else:raise RuntimeError('No authenticated master; compile not dispatched')
