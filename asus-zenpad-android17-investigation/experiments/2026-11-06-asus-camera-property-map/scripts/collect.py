from pathlib import Path
import importlib.util,sys,json,base64
sys.dont_write_bytecode=True
r=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('authorized_remote',r.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
script='''from pathlib import Path
import json,base64,hashlib,os,resource
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
r=Path('/srv/android/asus-camera-property-map-20261106')
files={}
for n in ['commands.json','input-pins.json','host-commands.json','abi-supplement-commands.json','binding.json','oem-vtable.json','supplement-input-pins.json','input-pins-post.json','oem-vector-symbols-relocs.txt','src/import-renames.txt']:
 p=r/n
 if p.is_file():files[n]=base64.b64encode(p.read_bytes()).decode()
for arch in ['arm','arm64']:
 for p in sorted((r/arch).glob('*')):
  if p.is_file(): files[arch+'/'+p.name]=base64.b64encode(p.read_bytes()).decode()
size=sum(p.stat().st_size for p in r.rglob('*') if p.is_file())
assert size<512*1024**2
print(json.dumps({'files':files,'scratch_bytes':size}))
'''
d=json.loads(m.run(script));total=0
for rel,data in d['files'].items():
 if rel.startswith(('arm/','arm64/')):dest=r/'artifacts'/rel
 elif rel=='src/import-renames.txt':dest=r/rel
 else:dest=r/'evidence'/rel
 dest.parent.mkdir(parents=True,exist_ok=True);b=base64.b64decode(data);dest.write_bytes(b);total+=len(b)
(r/'evidence/remote-budget.json').write_text(json.dumps({'scratch_bytes':d['scratch_bytes'],'limit_bytes':512*1024**2,'affinity':'one allowed CPU','address_space_bytes':1024**3,'script_cpu_seconds':120,'command_wall_seconds':45,'note':'No full build, target execution, loader, camera, or device commands.'},indent=2)+'\n')
print('Collected',len(d['files']),'selected new files,',total,'bytes; scratch',d['scratch_bytes'],'bytes')
