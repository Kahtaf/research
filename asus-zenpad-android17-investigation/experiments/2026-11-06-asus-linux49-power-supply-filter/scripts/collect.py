from pathlib import Path
import importlib.util,json,base64,hashlib,tarfile,io
R=Path(__file__).resolve().parents[1];W=R.parent;s=importlib.util.spec_from_file_location('fixed_remote',W/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
request='''from pathlib import Path
import base64,json,os,resource
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
O=Path('/srv/android/asus-linux49-power-supply-filter-20261106');print(json.dumps({n:base64.b64encode((O/n).read_bytes()).decode() for n in ['handoff.tar.gz','evidence/handoff.json','evidence/final-report.json']}))
'''
for name,b in json.loads(m.run(request)).items():
 p=R/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(b))
info=json.loads((R/'evidence/handoff.json').read_text());assert hashlib.sha256((R/'handoff.tar.gz').read_bytes()).hexdigest()==info['sha256']
with tarfile.open(R/'handoff.tar.gz') as t:
 for member in t.getmembers():
  assert not member.name.startswith('/') and '..' not in Path(member.name).parts
 t.extractall(R/'handoff',filter='data')
for name in ['preimage.c','postimage.c','filter.patch']:(R/'source'/name).write_bytes((R/'handoff/source'/name).read_bytes())
prior=W/'2026-11-06-asus-final-bpf-runtime';pins=json.loads((prior/'evidence/artifact-pins.json').read_text());qa={'handoff_archive_hash_valid':True,'prior_spike_all_recorded_files_unchanged':all(hashlib.sha256((prior/p).read_bytes()).hexdigest()==h for p,h in pins.items()),'owned_allocation_below_256MiB':info['allocation_bytes_including_archive']<=256*1024**2};assert all(qa.values()),qa;(R/'evidence/local-qa.json').write_text(json.dumps(qa,indent=2));print(json.dumps(dict(qa=qa,handoff=info),indent=2))
