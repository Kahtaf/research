from pathlib import Path
import json,hashlib,subprocess as s,tarfile,shutil,sys,re
R=Path('/srv/android/asus-firstboot-runtime');rev=sys.argv[1];assert re.fullmatch('r[0-9]+',rev);C=R/('capture-'+rev);C.mkdir();manifest=[]
def put(p,rel):
 b=p.read_bytes();d=C/rel;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(b);manifest.append(dict(path=str(rel),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
for p in (R/'source').glob('*'):
 if p.is_file():put(p,'source/'+p.name)
for p in (R/'evidence').glob('*'):
 if p.is_file():put(p,'evidence/'+p.name)
for run in sorted(R.glob('run-*')):
 for p in run.iterdir():
  if p.is_file() and (p.suffix in ['.json','.log','.txt','.c','.py']):put(p,'evidence/'+run.name+'/'+p.name)
for d in [R/'inputs/early-r1',*sorted((R/'inputs').glob('boot-*'))]:
 for p in d.glob('*.json'):put(p,'evidence/inputs/'+d.name+'/'+p.name)
 for p in d.glob('*.ninja-command'):put(p,'evidence/inputs/'+d.name+'/'+p.name)
for p in (R/'inputs/early-r1').glob('*.config'):put(p,'evidence/'+p.name)
put(R/'inputs/early-r1/root/policy','artifacts/precompiled_sepolicy')
elfs=[]
for p in (R/'inputs/early-r1/root').rglob('*'):
 if not p.is_file() or p.read_bytes()[:4]!=b'\x7fELF':continue
 dyn=s.check_output(['readelf','-d',str(p)],text=True);notes=s.check_output(['readelf','-n',str(p)],text=True)
 elfs.append(dict(path=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),needed=re.findall(r'Shared library: \[(.*?)\]',dyn),build_id=re.findall(r'Build ID: (\w+)',notes)))
(C/'evidence/elf-manifest.json').write_text(json.dumps(elfs,indent=2))
(C/'manifest.json').write_text(json.dumps(manifest,indent=2))
out=R/'artifacts'/('capture-'+rev+'.tar.gz')
with tarfile.open(out,'w:gz') as t:
 for p in sorted(C.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(C)))
print(json.dumps(dict(path=str(out),bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest(),manifest_entries=len(manifest))))
