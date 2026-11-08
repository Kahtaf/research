exec(open('2026-11-06-asus-r8-continuation-kit/preparation/inspect_remote.py').read().split('script=r')[0])
import base64
R=Path('2026-11-06-asus-r8-continuation-kit');payload={}
for folder in ['scripts','inputs/r8-preimages','inputs/r8-postimages','inputs/public-source','tests']:
 for f in (R/folder).rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts:payload[str(f.relative_to(R))]=base64.b64encode(f.read_bytes()).decode()
for n in ['plan.json','STAGED.json','r7-STAGED.json','r7-integration.json','r8-delta.json','r7-terminal-log.json']:payload['inputs/'+n]=base64.b64encode((R/'inputs'/n).read_bytes()).decode()
script='payload='+repr(payload)+r'''
from pathlib import Path
import json,hashlib,shutil,base64
R=Path('/srv/android/asus-reviewed-build-kit/r8');R.mkdir()
for folder in ['inputs','scripts','tests']:shutil.copytree(Path('/srv/android/asus-reviewed-build-kit/r7')/folder,R/folder)
for rel,b in payload.items():
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(b))
S=Path('/srv/android/asus-product-integration-staging/r8');shutil.copytree('/srv/android/asus-product-integration-staging/r7',S,symlinks=True)
for rel in json.loads((R/'inputs/r8-delta.json').read_text()):shutil.copyfile(R/'inputs/r8-postimages'/rel,S/'product-device'/rel)
shutil.copyfile(R/'inputs/STAGED.json',S/'STAGED.json')
import sys
sys.path.insert(0,str(R/'scripts'))
from integrate import manifest,write,sha
write(R/'inputs/r8-staging-manifest.json',manifest(S))
# Copy by exact previously recorded r7 verbose digest, even if a later parent m
# has rotated it. This is a preservation operation, not a live-build poll.
F=R/'evidence/r7-native';F.mkdir(parents=True)
expected='ac3b3a99e80ab47feef181073397fbc83837d6edcd035b30041913b5b01a77ee'
A=Path('/srv/android/lineage24/out')
found=[p for p in A.glob('verbose*.gz') if sha(p)==expected]
assert len(found)==1,'Authentic r7 verbose log unavailable; do not substitute current log'
shutil.copyfile(found[0],F/'verbose.log.gz');assert sha(F/'verbose.log.gz')==expected
prior=Path('/srv/android/asus-reviewed-build-kit/r7')
pins={group:{str(p):dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(files)} for group,files in [('attempt_files',[p for p in (prior/'attempt').rglob('*') if p.is_file()]),('logs',list(Path('/srv/android/asus-device-product/logs').glob('full-build-r7.*'))),('frozen_evidence',[F/'verbose.log.gz'])]}
write(R/'inputs/r7-preservation.json',pins)
print(json.dumps(dict(stage_files=len(manifest(S)),stage_manifest=json.loads((R/'inputs/r8-staging-manifest.json').read_text()),r7_preservation=pins,authentic_r7_verbose_found_at=str(found[0])),indent=2))
'''
r=m.run(script);(R/'evidence/staging-created.json').write_text(r);d=json.loads(r)
for n,key in [('r8-staging-manifest.json','stage_manifest'),('r7-preservation.json','r7_preservation')]:
 (R/'inputs'/n).write_text(json.dumps(d[key],indent=2,sort_keys=True)+'\n')
print(json.dumps(dict(stage_files=d['stage_files'],authentic_r7_verbose_found_at=d['authentic_r7_verbose_found_at'],preserved_attempt_files=len(d['r7_preservation']['attempt_files'])),indent=2))
