"""Authorized exact existing VM lifecycle around the one inherited helper compile."""
from pathlib import Path
import datetime,importlib.util,json,subprocess,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1]
retry=sys.argv[1:]==['--retry-after-ssh-timeout']
assert not sys.argv[1:] or retry
E=R/'evidence'
if retry:
 assert json.loads((E/'vm-lifecycle.json').read_text())['final_status']=='TERMINATED'
 assert 'ssh: connect to host IP_REDACTED port 22: Operation timed out' in (E/'compile-local.stderr.log').read_text()
 assert not (E/'compiler-receipt.json').exists() and not (R/'artifacts/init').exists()
 E=E/'vm-retry';E.mkdir()
VM='PROJECT_REDACTED'
ID='8549823276971553556'
OPTIONS=['--project=PROJECT_REDACTED','--zone=us-central1-a']
FIELDS='json(id,name,status,labels,zone,networkInterfaces)'
receipt=dict(instance=VM,id=ID,project='PROJECT_REDACTED',zone='us-central1-a',new_resources=False,resource_caps_changed=False,events=[])
assert not (E/'vm-lifecycle.json').exists(),'One lifecycle only'
def record():
 (E/'vm-lifecycle.json').write_text(json.dumps(receipt,indent=2)+'\n')
def run(args,name):
 q=subprocess.run(args,capture_output=True,text=True)
 (E/(name+'.stdout.log')).write_text(q.stdout)
 (E/(name+'.stderr.log')).write_text(q.stderr)
 receipt['events'].append(dict(command=args,exit=q.returncode,at=datetime.datetime.now(datetime.timezone.utc).isoformat()))
 record()
 q.check_returncode()
 return q.stdout
def identity(data,status):
 assert data['id']==ID and data['name']==VM and data['status']==status
 assert data['zone'].endswith('/projects/PROJECT_REDACTED/zones/us-central1-a')
 assert all(data['labels'].get(k)==v for k,v in dict(owner='kahtaf',purpose='rom-build',expires='2026-11-12').items())
 assert data['networkInterfaces'][0]['accessConfigs'][0]['natIP']=='IP_REDACTED'
before_path=R/'evidence/vm-after.stdout.log' if retry else E/'vm-before.json'
before=json.loads(before_path.read_text());identity(before,'TERMINATED')
receipt['pre_start_identity_verified']=True;record()
try:
 run(['gcloud','compute','instances','start',VM,*OPTIONS],'vm-start')
 data=json.loads(run(['gcloud','compute','instances','describe',VM,*OPTIONS,'--format='+FIELDS],'vm-running'))
 identity(data,'RUNNING');receipt['running_identity_verified']=True;record()
 if retry:
  rp=R.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py'
  spec=importlib.util.spec_from_file_location('readiness_remote',rp);remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
  ready=False
  for attempt in range(1,4):
   try:
    assert remote.run("print('OWNED_COMPILE_SSH_READY')").strip()=='OWNED_COMPILE_SSH_READY'
    (E/('ssh-ready-'+str(attempt)+'.log')).write_text('Exact existing remote.py SSH connected; no compiler invoked by readiness.\n');ready=True;break
   except RuntimeError as exc:
    (E/('ssh-ready-'+str(attempt)+'.log')).write_text(str(exc)+'\n')
  assert ready,'Bounded SSH readiness exhausted; no compile'
 run([sys.executable,'-B',str(R/'scripts/compile_once.py'),*(['--retry-ssh-only'] if retry else [])],'compile-local')
 receipt['compile_and_small_fetch_completed']=True
finally:
 # The same exact name/id was verified before start; no other VM is selected.
 run(['gcloud','compute','instances','stop',VM,*OPTIONS],'vm-stop')
 data=json.loads(run(['gcloud','compute','instances','describe',VM,*OPTIONS,'--format='+FIELDS],'vm-after'))
 identity(data,'TERMINATED');receipt['final_status']='TERMINATED';record()
print(json.dumps(receipt,indent=2))
