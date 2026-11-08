exec(open('2026-11-06-asus-r8-continuation-kit/preparation/inspect_remote.py').read().split('script=r')[0])
import base64,hashlib
R=Path('2026-11-06-asus-r8-continuation-kit');files=[R/n for n in ['README.md','HANDOFF.md','REPORT.md','kit-seal.json']]
for d in ['source','evidence','artifacts']:
 files.extend(p for p in (R/d).rglob('*') if p.is_file())
payload={str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode() for p in files}
r=m.run('payload='+repr(payload)+r'''
from pathlib import Path
import base64,json,sys,hashlib
R=Path('/srv/android/asus-reviewed-build-kit/r8');sys.path.insert(0,str(R/'scripts'))
from integrate import verify_pins,read,sha,write
assert verify_pins(R)=='f55aedf8ac9d2a513e3663230db0b9d802e72b5df512fc0db6b3714331a7efa4'
assert not (R/'attempt').exists() and not (R/'parent-review').exists()
equivalent_json=[]
for rel,data in payload.items():
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True);b=base64.b64decode(data)
 if p.exists():
  if p.read_bytes()!=b:
   assert p.suffix=='.json' and json.loads(p.read_bytes())==json.loads(b),'Existing own evidence differs: '+rel
   equivalent_json.append(dict(path=rel,local_sha256=hashlib.sha256(b).hexdigest(),preserved_vm_sha256=sha(p)))
 else:
  with p.open('xb') as f:f.write(b)
assert sha(R/'artifacts/r8-continuation-compact.tar.gz')=='413e55c74e90bea3d400ec8b9beaf40f57d2f9e12298e1de08fbd0e557c2e61f'
result=dict(status='SEALED_R8_REVIEW_PACKAGE_PRESENT',kit_pins_sha256=verify_pins(R),archive_sha256=sha(R/'artifacts/r8-continuation-compact.tar.gz'),documents_and_artifacts=len(payload),equivalent_json_with_original_vm_format_preserved=equivalent_json,r8_attempt_exists=False,parent_acceptance_authored=False,product_build_started=False)
write(R/'evidence/review-package-present.json',result);print(json.dumps(result,indent=2))
''');(R/'evidence/review-package-present.json').write_text(r);print(r)
