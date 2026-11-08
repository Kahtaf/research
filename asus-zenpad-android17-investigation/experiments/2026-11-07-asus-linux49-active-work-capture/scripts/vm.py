from pathlib import Path
import datetime, importlib.util, json, os, subprocess, sys, time
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('unchanged_remote',R.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
SSH=remote.SSH
VM='PROJECT_REDACTED';OPT=['--project=PROJECT_REDACTED','--zone=us-central1-a']
def run(cmd,name,timeout=None):
 q=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
 (R/'evidence'/(name+'.stdout')).write_text(q.stdout);(R/'evidence'/(name+'.stderr')).write_text(q.stderr)
 with (R/'evidence/lifecycle.jsonl').open('a') as f:f.write(json.dumps(dict(phase=name,exit=q.returncode,at=datetime.datetime.now(datetime.timezone.utc).isoformat()))+'\n')
 return q
def identity(status,name):
 q=run(['gcloud','compute','instances','describe',VM,*OPT,'--format=json(id,status,labels,networkInterfaces)'],name);q.check_returncode();d=json.loads(q.stdout)
 assert d['id']=='8549823276971553556' and d['status']==status
 assert all(d['labels'].get(k)==v for k,v in {'owner':'kahtaf','purpose':'rom-build','expires':'2026-11-12'}.items())
 assert d['networkInterfaces'][0]['accessConfigs'][0]['natIP']=='IP_REDACTED'
def channel():
 assert (R/'s').is_socket(),'No master: no TCP fallback'
 return SSH[:-1]+['-S','s','-o','ControlMaster=no','-o','ProxyCommand=false']+SSH[-1:]
if __name__=='__main__':
 os.chdir(R)
 if sys.argv[1]=='start':
  assert not (R/'evidence/start.stdout').exists()
  identity('TERMINATED','before');run(['gcloud','compute','instances','start',VM,*OPT],'start').check_returncode();identity('RUNNING','running')
  for n in range(1,10):
   q=run(SSH[:-1]+['-M','-S','s','-o','ControlPersist=yes','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=12','-f','-N',SSH[-1]],'master-'+str(n),25)
   if q.returncode==0:break
   time.sleep(5)
  assert (R/'s').is_socket()
  run(SSH[:-1]+['-S','s','-O','check',SSH[-1]],'master-check',10).check_returncode()
  print('Authenticated master ready; compiler TCP fallback disabled')
 elif sys.argv[1]=='stop':
  if (R/'s').is_socket():run(SSH[:-1]+['-S','s','-O','exit',SSH[-1]],'master-exit',10)
  run(['gcloud','compute','instances','stop',VM,*OPT],'stop').check_returncode();identity('TERMINATED','after');print('Verified TERMINATED')
