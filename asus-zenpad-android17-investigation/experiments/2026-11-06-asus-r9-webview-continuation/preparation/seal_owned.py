from pathlib import Path
import base64,json,hashlib
import remote
R=Path(__file__).resolve().parents[1]
# Never export or pin the 260 MB VM payload as local content.
files={str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode() for folder in ['source'] for p in (R/folder).rglob('*') if p.is_file()}
for n in ['README.md','REPORT.md','HANDOFF.md','CACHE-PROVENANCE-GAP.md','inputs/webview-origin.json','evidence/inherited-guards.json','evidence/parent-r8-facts-reference.json','evidence/parent-input-acceptance-reference.json']:files[n]=base64.b64encode((R/n).read_bytes()).decode()
s='FILES='+repr(files)+'\n'+r'''
from pathlib import Path
import base64,json,hashlib,sys,ast,subprocess
R=Path('/srv/android/asus-reviewed-build-kit/r9')
assert not (R/'inputs/kit-pins.json').exists()
# Seal only after actual final audit and dependency scan terminate successfully.
for name in ['final-source-audit.json','selected-lfs-product-audit.json','linux-tests-seal.json']:
 assert (R/'evidence'/name).is_file(),name
assert json.loads((R/'evidence/linux-tests-seal.json').read_text())['exit_code']==0
assert json.loads((R/'evidence/selected-lfs-product-audit.json').read_text())['additional_needed_materializations']==[]
assert json.loads((R/'evidence/final-source-audit.json').read_text())['active_source_and_current_ninja_scope_unchanged'] is True
for rel,b in FILES.items():
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(base64.b64decode(b))
for p in (R/'scripts').glob('*.py'):ast.parse(p.read_text(),filename=str(p))
assert subprocess.run(['bash','-n',str(R/'scripts/build.sh')]).returncode==0
# Bind compact new qualification receipts as kit inputs. Preserve old qualification.
q=R/'inputs/qualification/r9';q.mkdir()
for name in ['artifact-check.json','lineage-lfs-batch.json','cache-gap.json','cache-current-identity.json','cache-provenance-gap.json','selected-siso-state-v2.json','selected-siso-dependencies.json','siso-schema-routes.json','siso-hash-semantics.json','siso-step-manifest-semantics.json','cleanup-summary.json','selected-lfs-product-audit.json','final-source-audit.json','linux-tests-seal.json']:
 with (q/name).open('xb') as out:out.write((R/'evidence'/name).read_bytes())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
pins={}
for folder in ['scripts','inputs','tests','source','evidence']:
 for p in sorted((R/folder).rglob('*')):
  if p.is_file() and p.name!='kit-pins.json' and '__pycache__' not in p.parts:pins[str(p.relative_to(R))]=sha(p)
for name in ['README.md','REPORT.md','HANDOFF.md','CACHE-PROVENANCE-GAP.md']:pins[name]=sha(R/name)
with (R/'inputs/kit-pins.json').open('x') as f:json.dump(pins,f,indent=2,sort_keys=True);f.write('\n')
sys.path.insert(0,str(R/'scripts'))
from integrate import verify_pins,read
from continuation import preservation
preservation(read(R/'inputs/plan.json'))
for path,pin in json.loads((R/'evidence/actual-audit.json').read_text())['source_scope_pins'].items():assert sha(Path(path))==pin['sha256'],path
assert sha(Path('/srv/android/lineage24/out/.siso_fs_state'))==json.loads((R/'evidence/selected-siso-state-v2.json').read_text())['source_state_sha256']
assert sha(Path('/srv/android/lineage24/out/.siso_deps'))==json.loads((R/'evidence/selected-siso-dependencies.json').read_text())['source_deps_sha256']
seal=verify_pins(R)
assert not (R/'attempt').exists() and not (R/'parent-review').exists()
r=dict(kit_pins_sha256=seal,pinned_files=len(pins),kit=str(R),artifact_path='/srv/android/asus-product-integration-staging/r9/webview.apk',artifact_sha256='1d2f61832b2596b0046cb82cf3634609ea866098d097a83fac27c35272ac726a',artifact_bytes=260835655,status='SEALED_PREPARATION_BLOCKED_CACHE_LINEAGE',parent_approved=False,integration=False,native_build=False,physical_go=False)
with (R/'kit-seal.json').open('x') as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps(dict(receipt=r,manifest=pins),indent=2))
'''
r=json.loads(remote.run(s));(R/'kit-seal.json').write_text(json.dumps(r['receipt'],indent=2,sort_keys=True)+'\n');(R/'inputs/kit-pins.json').write_text(json.dumps(r['manifest'],indent=2,sort_keys=True)+'\n');print(json.dumps(r['receipt'],indent=2))
