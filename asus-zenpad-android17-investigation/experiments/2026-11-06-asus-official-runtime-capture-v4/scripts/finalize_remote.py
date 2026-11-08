"""Seal own preparation after serial QA; transfer compact receipts only."""
import base64,hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('remote',ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
files={}
for p in [ROOT/'HANDOFF.json',ROOT/'REPORT.md']+sorted((ROOT/'evidence').glob('*')):
 if p.is_file():files[str(p.relative_to(ROOT))]=base64.b64encode(p.read_bytes()).decode()
script=r'''import base64,datetime,hashlib,json,os,resource,subprocess,sqlite3
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(120,120))
root=Path('/srv/android/asus-official-runtime-capture/preparation-v4')
if root.resolve()!=root or (root/'FINALIZED.json').exists():raise RuntimeError('fresh finalization only')
for name,data in json.loads(DATA).items():
 path=root/name;encoded=base64.b64decode(data)
 if path.exists():
  if path.read_bytes()!=encoded:raise RuntimeError('preserve existing evidence: '+name)
 else:
  with path.open('xb') as f:f.write(encoded)
pins=json.loads((root/'tool-pins.json').read_bytes())
for name,digest in pins.items():
 if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('tool drift: '+name)
qa=json.loads((root/'evidence/linux-qa-execution-final.json').read_bytes())
if qa['returncode'] or qa['tested_pins']!=pins or qa['changed_during_tests']:raise RuntimeError('final candidate not exactly Linux tested')
seal=hashlib.sha256((root/'tool-pins.json').read_bytes()).hexdigest()
if seal!=json.loads((root/'HANDOFF.json').read_bytes())['tool_seal_sha256']:raise RuntimeError('handoff seal')
p=subprocess.run(['python3','-B',str(root/'source/capture.py')],capture_output=True,text=True,check=True,timeout=10)
plan=json.loads(p.stdout)
if plan['mode']!='PLAN_ONLY' or plan['source_or_output_inspected'] or plan['lock_acquired']:raise RuntimeError('static plan boundary')
full=json.loads((root/'graph-qualification-003/qualification.json').read_bytes())
if not full['all_graph_includes_indexed'] or full['sqlite_integrity_check']!='ok' or full['source_before']!=full['source_after'] or any('error' in r for r in full['selector_producer_resolutions']):raise RuntimeError('real graph resource/known-producer qualification blocker')
projection=json.loads((root/'graph-provenance-004/qualification.json').read_bytes())
if projection['status']!='GRAPH_RESOLUTION_BLOCKER' or not projection['errors']:raise RuntimeError('preserve disclosed provenance blockers')
if full['tested_module_sha256']!={n:hashlib.sha256((root/'source'/n).read_bytes()).hexdigest() for n in ('graph.py','safeio.py')}:raise RuntimeError('graph module drift')
# Rehash only the owned read-only frozen files; never revisit actual output payloads.
import sys
sys.path.insert(0,str(root/'source'))
from safeio import Tree,fingerprint
frozen=Tree(root/'graph-qualification-003/frozen')
for name,pin in full['frozen'].items():
 if frozen.digest(name,plan['profile']['limits']['graph_file_bytes'])!=pin:raise RuntimeError('frozen drift')
frozen.close()
db=sqlite3.connect('file:'+str(root/'graph-qualification-003/graph-index.sqlite')+'?mode=ro&immutable=1',uri=True)
page_size=db.execute('PRAGMA page_size').fetchone()[0];page_count=db.execute('PRAGMA page_count').fetchone()[0];db.close()
if page_size*page_count!=full['index_bytes'] or full['index_bytes']>plan['profile']['limits']['index_bytes']:raise RuntimeError('index size')
index_path=root/'graph-qualification-003/graph-index.sqlite'
index_hash=hashlib.sha256()
with index_path.open('rb') as f:
 before=fingerprint(os.fstat(f.fileno()))
 for block in iter(lambda:f.read(1024*1024),b''):index_hash.update(block)
 if before!=fingerprint(os.fstat(f.fileno())) or before!=fingerprint(index_path.stat()):raise RuntimeError('index drift')
storage_bytes=sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
if storage_bytes>48*1024**3:raise RuntimeError('48 GiB total owned preparation budget')
receipt={'index_sha256':index_hash.hexdigest(),'index_bytes':before[3],'owned_preparation_storage_bytes':storage_bytes,'owned_storage_hard_budget_bytes':48*1024**3,'schema':1,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'preparation':str(root),'tool_seal_sha256':seal,'all_final_tool_pins_match':True,'all_final_pins_exactly_linux_tested':True,'graph_module_exactly_real_scale_tested':True,'graph_resource_qualification_passed':True,'full_capture_provenance_qualified':False,'provenance_projection_blocker_count':len(projection['errors']),'frozen_graphs_rehashed':len(full['frozen']),'actual_select_verify_copy_executed':False,'static_plan_only':True,'r8_failed_parent_report_preserved':True,'future_r9_profile_created':False,'runtime_ready':False,'physical_GO':False,'only_owned_v4_prefix_written':True,'cpu_count':len(os.sched_getaffinity(0)),'address_space_limit_bytes':resource.getrlimit(resource.RLIMIT_AS)[0]}
with (root/'FINALIZED.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
print(json.dumps(receipt,indent=2))
'''.replace('DATA',repr(json.dumps(files)))
r=json.loads(remote.run(script))
with (ROOT/'evidence/preparation-verification.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
