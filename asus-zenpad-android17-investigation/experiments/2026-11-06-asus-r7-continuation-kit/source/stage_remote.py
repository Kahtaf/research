from pathlib import Path
import importlib.util,json
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('remote',R/'scripts/remote.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
code='''
from pathlib import Path
import hashlib,json,os,resource,shutil
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1073741824,1073741824))
A=Path('/srv/android/asus-product-integration-staging/r3');B=Path('/srv/android/asus-product-integration-staging/r7')
assert not B.exists(), 'own r7 staging already exists; do not overwrite'
shutil.copytree(A,B,symlinks=True)
F=B/'product-device/sensors/BoardConfig.mk'
assert hashlib.sha256(F.read_bytes()).hexdigest()=='0e012287927a5b8ac3733f7fcc28d5cdc0eb1d8f06e82e0ff6ad211fe2f72f90'
data=F.read_bytes();old=b'P00A_ACCEL_BOARD_PATH := $(call my-dir)\\n';new=b'P00A_ACCEL_BOARD_PATH := device/asus/p00a/sensors\\n'
assert data.count(old)==1
F.write_bytes(data.replace(old,new))
assert hashlib.sha256(F.read_bytes()).hexdigest()=='9207c304761cf86afb423641534ed383e7f8dae613e64061e972d2f65832aa4d'
for name,key in [('STAGED.json','product_after'),('sensor-selection.json','files')]:
 p=B/name;d=json.loads(p.read_text());d[key]['sensors/BoardConfig.mk' if key=='product_after' else 'BoardConfig.mk']={'sha256':hashlib.sha256(F.read_bytes()).hexdigest()}
 if name=='sensor-selection.json':d['board_path_adjustment']='One exact reviewed assignment replaces unavailable my-dir; policy and manifest unchanged'
 p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\\n')
def manifest(root):
 return {str(p.relative_to(root)):({'symlink':os.readlink(p)} if p.is_symlink() else {'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}) for p in sorted(root.rglob('*')) if p.is_file() or p.is_symlink()}
a=manifest(A);b=manifest(B)
assert set(a)==set(b)
changed=[p for p in a if a[p]!=b[p]]
assert changed==['STAGED.json','product-device/sensors/BoardConfig.mk','sensor-selection.json'],changed
soong=Path('/srv/android/lineage24/build/make/core/soong_config.mk').read_text().splitlines()
lines=[{'line':i+1,'text':s} for i,s in enumerate(soong) if any(x in s.lower() for x in ['sepolicy','manifestfile','manifest_file'])]
print(json.dumps({'manifest':b,'ancestor_manifest':a,'changed':changed,'soong_policy_manifest_lines':lines}))
'''
r=json.loads(m.run(code));(R/'evidence/staging-created.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');(R/'inputs/r7-staging-manifest.json').write_text(json.dumps(r['manifest'],indent=2,sort_keys=True)+'\n');(R/'inputs/r3-staging-manifest.json').write_text(json.dumps(r['ancestor_manifest'],indent=2,sort_keys=True)+'\n');print(json.dumps({'files':len(r['manifest']),'changed':r['changed'],'soong':r['soong_policy_manifest_lines']},indent=2))
