"""Single-use identity corroboration. No process, log, status or terminal reads."""
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
receipt=ROOT/'evidence/r8-identity-once.json'
if receipt.exists():raise SystemExit('Already corroborated; do not reread build metadata')
spec=importlib.util.spec_from_file_location('parent_remote',ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
script=r'''import datetime,hashlib,json,os,resource
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
owned=Path('/srv/android/asus-official-runtime-capture/preparation-v3/evidence/r8-identity-once.json')
if owned.exists():raise RuntimeError('Already corroborated; no repeat reads')
paths=[Path('/srv/android/asus-reviewed-build-kit/r8/attempt/launch.json'),Path('/srv/android/asus-device-product/logs/full-build-r8.pid')]
rows=[]
for path in paths:
 if path.resolve()!=path:raise RuntimeError('metadata path must be canonical')
 try:
  fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
 except FileNotFoundError:
  rows.append({'path':str(path),'present':False});continue
 with os.fdopen(fd,'rb') as f:data=f.read(65537)
 if len(data)>65536:raise RuntimeError('metadata bound exceeded')
 rows.append({'path':str(path),'present':True,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'text':data.decode()})
if all(r['present'] for r in rows):
 launch=json.loads(rows[0]['text']);child=int(rows[1]['text'].strip())
 if launch!={'revision':'r8','lock_inode':15018964,'supervisor_pid':1580911} or child!=1581077:raise RuntimeError('r8 identity disagrees with parent metadata')
 status='corroborated'
else:status='pending_parent_metadata'
receipt={'schema':1,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,'immutable_metadata_reads_once':True,'files':rows,'progress_or_process_reads':False,'terminal_result_inferred':False,'actual_output_operations':False,'cpu_count':len(os.sched_getaffinity(0)),'address_space_limit_bytes':resource.getrlimit(resource.RLIMIT_AS)[0]}
with owned.open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
print(json.dumps(receipt))
'''
result=json.loads(remote.run(script))
with receipt.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
