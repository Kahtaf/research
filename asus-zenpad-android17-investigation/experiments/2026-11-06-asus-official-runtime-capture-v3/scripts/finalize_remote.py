"""Finalize only documentation/identity/seal and append compact own-prefix receipts."""
import base64
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('parent_remote',ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
files={}
for name in ('README.md','inputs/fixed-r8-metadata.json','tool-pins.json','HANDOFF.json','REPORT.md'):
    files[name]=base64.b64encode((ROOT/name).read_bytes()).decode()
for folder in ('evidence','scripts'):
    for p in sorted((ROOT/folder).glob('*')):
        if p.is_file():files[str(p.relative_to(ROOT))]=base64.b64encode(p.read_bytes()).decode()
script=r'''import base64,datetime,hashlib,json,os,resource,subprocess
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
root=Path('/srv/android/asus-official-runtime-capture/preparation-v3')
if root.resolve()!=root:raise RuntimeError('noncanonical preparation')
old_bytes=(root/'tool-pins.json').read_bytes()
if hashlib.sha256(old_bytes).hexdigest()!='bdde8926c4a354bf3917a1810c9ccdd372fa1e91788b18a7c8e1c96561917daf':raise RuntimeError('unexpected candidate seal')
old=json.loads(old_bytes)
for name,digest in old.items():
 if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('candidate drift: '+name)
files=json.loads(PAYLOAD)
replacements={'README.md','inputs/fixed-r8-metadata.json','tool-pins.json'}
for name,encoded in files.items():
 path=root/name;data=base64.b64decode(encoded)
 path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 if path.exists():
  if path.read_bytes()==data:continue
  if name not in replacements:raise RuntimeError('existing evidence drift: '+name)
  with path.open('wb') as f:f.write(data)
 else:
  with path.open('xb') as f:f.write(data)
pins=json.loads((root/'tool-pins.json').read_bytes())
for name,digest in pins.items():
 if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('final drift: '+name)
qa=json.loads((root/'evidence/linux-qa-execution.json').read_bytes())
changes=[name for name in pins if pins[name]!=qa['tested_pins'][name]]
if changes!=['README.md','inputs/fixed-r8-metadata.json']:raise RuntimeError('untested code change')
argv=['python3','-B',str(root/'source/capture.py')]
p=subprocess.run(argv,text=True,capture_output=True,timeout=10,check=True)
plan=json.loads(p.stdout)
if plan['mode']!='PLAN_ONLY' or plan['source_or_output_inspected'] or plan['lock_acquired']:raise RuntimeError('static plan boundary')
if plan['profile']['pids']!=[1580911,1581077] or plan['profile']['revision']!='r8':raise RuntimeError('profile identity')
seal=hashlib.sha256((root/'tool-pins.json').read_bytes()).hexdigest()
if seal!=json.loads((root/'HANDOFF.json').read_bytes())['tool_seal_sha256']:raise RuntimeError('handoff seal')
receipt={'schema':1,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'preparation':str(root),'tool_seal_sha256':seal,'all_final_tool_pins_match':True,'final_pins':pins,'executable_selector_profile_tests_equal_linux_tested_candidate':True,'post_qa_changes':changes,'static_plan_returncode':p.returncode,'source_or_output_inspected':False,'lock_acquired':False,'actual_select_verify_copy_executed':False,'only_new_preparation_written':True,'cpu_count':len(os.sched_getaffinity(0)),'address_space_limit_bytes':resource.getrlimit(resource.RLIMIT_AS)[0]}
with (root/'evidence/preparation-verification.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
print(json.dumps(receipt))
'''.replace('PAYLOAD',repr(json.dumps(files)))
result=json.loads(remote.run(script))
with (ROOT/'evidence/preparation-verification.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='final_pins'}))
