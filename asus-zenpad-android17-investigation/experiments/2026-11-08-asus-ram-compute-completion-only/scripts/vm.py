from pathlib import Path
import datetime,hashlib,importlib.util,json,os,subprocess,sys,time
R=Path(__file__).resolve().parents[1]
p=R.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab'
spec=importlib.util.spec_from_file_location('unchanged_remote',p);remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
SSH=remote.SSH;SOCK='/tmp/ascomp-342c9034';VM='PROJECT_REDACTED';OPT=['--project=PROJECT_REDACTED','--zone=us-central1-a']
def run(cmd,name,timeout=None):
 q=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
 (R/'evidence'/(name+'.stdout')).write_text(q.stdout);(R/'evidence'/(name+'.stderr')).write_text(q.stderr)
 with (R/'evidence/lifecycle.jsonl').open('a') as f:f.write(json.dumps(dict(phase=name,exit=q.returncode,at=datetime.datetime.now(datetime.timezone.utc).isoformat()))+'\n')
 return q
def identity(status,name):
 q=run(['gcloud','compute','instances','describe',VM,*OPT,'--format=json(id,status,networkInterfaces)'],name);q.check_returncode();d=json.loads(q.stdout)
 assert d['id']=='8549823276971553556' and d['status']==status
 assert d['networkInterfaces'][0]['accessConfigs'][0]['natIP']=='IP_REDACTED'
def channel():
 assert Path(SOCK).is_socket(),'No owned master; no TCP fallback'
 return SSH[:-1]+['-S',SOCK,'-o','ControlMaster=no','-o','ProxyCommand=false']+SSH[-1:]
if __name__=='__main__':
 if sys.argv[1]=='start':
  assert not Path(SOCK).exists() and not (R/'evidence/start.stdout').exists()
  identity('TERMINATED','before');run(['gcloud','compute','instances','start',VM,*OPT],'start').check_returncode();identity('RUNNING','running')
  for n in range(1,10):
   q=run(SSH[:-1]+['-M','-S',SOCK,'-o','ControlPersist=yes','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=12','-f','-N',SSH[-1]],'master-'+str(n),25)
   if not q.returncode:break
   if 'Permission denied' in q.stderr:
    identity('RUNNING','auth-failure-identity');raise RuntimeError('Authentication failed: '+q.stderr)
   time.sleep(5)
  assert Path(SOCK).is_socket()
  run(SSH[:-1]+['-S',SOCK,'-O','check',SSH[-1]],'master-check',10).check_returncode()
  print('Owned persistent master ready')
 elif sys.argv[1]=='stop':
  if Path(SOCK).is_socket():run(SSH[:-1]+['-S',SOCK,'-O','exit',SSH[-1]],'master-exit',10).check_returncode()
  run(['gcloud','compute','instances','stop',VM,*OPT],'stop').check_returncode();identity('TERMINATED','after');print('Verified TERMINATED')
