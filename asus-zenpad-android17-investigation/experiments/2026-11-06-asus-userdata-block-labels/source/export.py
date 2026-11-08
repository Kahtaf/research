from pathlib import Path
import importlib.util,sys,json,base64,hashlib
sys.dont_write_bytecode=True
r=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('authorized_remote',r.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
script='''import pathlib,json,base64,os,resource
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(30,30))
R=pathlib.Path('/srv/android/asus-userdata-block-labels-20261106')
paths=list((R/'inputs').rglob('*'))+list((R/'current').glob('*'))+[R/n for n in ['candidate.patch','candidate-device-file_contexts','fixture-only-vendor_file_contexts','native-evidence-attempt2.json']]
print(json.dumps({str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode()for p in paths if p.is_file() and p.name!='precompiled_sepolicy'}))
'''
(r/'source/export_remote.py').write_text(script)
data=json.loads(m.run(script));manifest=[]
for name,encoded in data.items():
 dest=r/('candidate' if name.startswith('candidate') else 'evidence/snapshots')/name;dest.parent.mkdir(parents=True,exist_ok=True);b=base64.b64decode(encoded);dest.write_bytes(b);manifest.append(dict(path=str(dest.relative_to(r)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
(r/'evidence/export-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'exported_files':len(manifest),'exported_bytes':sum(p['bytes']for p in manifest)}))
