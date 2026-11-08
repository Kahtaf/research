"""Exact authorized VM lifecycle, bounded readiness, one helper compile/fetch."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,signal,subprocess,sys,time
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];E=R/'evidence'
VM='PROJECT_REDACTED';ID='8549823276971553556'
OPTIONS=['--project=PROJECT_REDACTED','--zone=us-central1-a']
FIELDS='json(id,name,status,labels,zone,networkInterfaces)'
receipt=dict(instance=VM,id=ID,project='PROJECT_REDACTED',zone='us-central1-a',events=[],new_resources=False,resource_caps_changed=False,readiness_limit_seconds=180)
assert not (E/'vm-lifecycle.json').exists(),'One lifecycle only'
assert not (E/'compile-dispatch.json').exists(),'One compiler dispatch only'
assert json.loads((E/'source-scope-receipt.json').read_text())['source_sha256']==hashlib.sha256((R/'source/init.c').read_bytes()).hexdigest()
def record():
 (E/'vm-lifecycle.json').write_text(json.dumps(receipt,indent=2)+'\n')
def run(args,name):
 q=subprocess.run(args,capture_output=True,text=True)
 (E/(name+'.stdout.log')).write_text(q.stdout);(E/(name+'.stderr.log')).write_text(q.stderr)
 receipt['events'].append(dict(command=args,exit=q.returncode,at=datetime.datetime.now(datetime.timezone.utc).isoformat()));record();q.check_returncode();return q.stdout
def identity(data,status):
 assert data['id']==ID and data['name']==VM and data['status']==status
 assert data['zone'].endswith('/projects/PROJECT_REDACTED/zones/us-central1-a')
 assert all(data['labels'].get(k)==v for k,v in dict(owner='kahtaf',purpose='rom-build',expires='2026-11-12').items())
 assert data['networkInterfaces'][0]['accessConfigs'][0]['natIP']=='IP_REDACTED'
identity(json.loads((E/'vm-before.json').read_text()),'TERMINATED')
receipt['pre_start_identity_verified']=True;record()
rp=R.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py'
assert hashlib.sha256(rp.read_bytes()).hexdigest()=='c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab'
spec=importlib.util.spec_from_file_location('readiness_remote',rp);remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
try:
 run(['gcloud','compute','instances','start',VM,*OPTIONS],'vm-start')
 started=time.monotonic()
 data=json.loads(run(['gcloud','compute','instances','describe',VM,*OPTIONS,'--format='+FIELDS],'vm-running'))
 identity(data,'RUNNING');receipt['running_identity_verified']=True;record()
 attempt=0;ready=False
 while time.monotonic()-started<180:
  attempt+=1;at=time.monotonic();remaining=180-(at-started)
  if remaining<16:break
  print('SSH readiness probe '+str(attempt),flush=True)
  try:
   code="import importlib.util; s=importlib.util.spec_from_file_location('r',"+repr(str(rp))+"); r=importlib.util.module_from_spec(s); s.loader.exec_module(r); print(r.run(\"print('OWNED_COMPILE_SSH_READY')\"),end='')"
   q=subprocess.Popen([sys.executable,'-B','-c',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
   try:out,err=q.communicate(timeout=min(20,remaining))
   except subprocess.TimeoutExpired:
    os.killpg(q.pid,signal.SIGKILL);out,err=q.communicate();raise RuntimeError('Bounded readiness SSH timeout\n'+out+err)
   assert q.returncode==0 and out.strip()=='OWNED_COMPILE_SSH_READY',out+err
   (E/('ssh-ready-'+str(attempt)+'.log')).write_text('Existing unchanged remote.py connected; readiness invoked no compiler.\n');ready=True;break
  except Exception as exc:
   (E/('ssh-ready-'+str(attempt)+'.log')).write_text(str(exc)+'\n')
  delay=min(max(0,10-(time.monotonic()-at)),max(0,180-(time.monotonic()-started)))
  if delay:time.sleep(delay)
 receipt.update(ssh_readiness_attempts=attempt,ssh_ready=ready,readiness_elapsed_seconds=time.monotonic()-started);record()
 assert ready,'Readiness exhausted before compiler dispatch'
 run([sys.executable,'-B',str(R/'scripts/compile_once.py')],'compile-local')
 receipt['compile_and_small_fetch_completed']=True;record()
finally:
 run(['gcloud','compute','instances','stop',VM,*OPTIONS],'vm-stop')
 data=json.loads(run(['gcloud','compute','instances','describe',VM,*OPTIONS,'--format='+FIELDS],'vm-after'))
 identity(data,'TERMINATED');receipt['final_status']='TERMINATED';record()
print(json.dumps(receipt,indent=2),flush=True)
