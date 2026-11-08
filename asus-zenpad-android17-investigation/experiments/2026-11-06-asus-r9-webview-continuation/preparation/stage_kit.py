from pathlib import Path
import remote,json,base64
R=Path(__file__).resolve().parents[1]
files={str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode() for p in (R/'scripts').glob('*') if p.is_file()}
evidence={p.name:base64.b64encode(p.read_bytes()).decode() for p in (R/'evidence').glob('*.json') if p.name not in ['initial.json','initial-bounded.json']}
s=r'''
from pathlib import Path
import shutil,json,base64,sys
R=Path('/srv/android/asus-reviewed-build-kit/r9');OLD=Path('/srv/android/asus-reviewed-build-kit/r8')
# Copy inert kit inputs only, not source trees, attempts, checkouts, or credentials.
for src in (OLD/'inputs').iterdir():
 if src.name=='kit-pins.json':continue
 dst=R/'inputs'/src.name
 if src.is_dir():shutil.copytree(src,dst)
 else:
  with src.open('rb') as inp,dst.open('xb') as out:shutil.copyfileobj(inp,out,1048576)
for rel,b in FILES.items():
 with (R/rel).open('xb') as f:f.write(base64.b64decode(b))
for name,b in EVIDENCE.items():
 p=R/'evidence'/name
 if not p.exists():
  with p.open('xb') as f:f.write(base64.b64decode(b))
plan=json.loads((OLD/'inputs/plan.json').read_text());plan.update(revision='r9',prior_revision='r8',run_root=str(R),r8_kit=str(OLD),r8_integration=str(R/'inputs/r8-integration.json'),r8_preservation=str(R/'inputs/r8-preservation.json'),r9_delta=str(R/'inputs/r9-delta.json'),artifact_staging='/srv/android/asus-product-integration-staging/r9/webview.apk',original_pids=plan['original_pids']+[1580911,1581077],parent_contract='Artifact exact admission passed. Parent-only terminal review and continuous original lock. CACHE_LINEAGE_INCOMPLETE prevents integration/launch; no bypass.')
(R/'inputs/plan.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')
shutil.copyfile(OLD/'attempt/integration.json',R/'inputs/r8-integration.json')
audit=json.loads((R/'evidence/actual-audit.json').read_text())
for name,data in [('r8-preservation.json',dict(attempt_files=audit['preservation'],logs=audit['logs'])),('r9-delta.json',{'external/chromium-webview/prebuilt/arm64/webview.apk':dict(before_sha256='a7b12c1895a3b354a91997fffe0e383a88e5b0e0d4371f8fdc090c71f62aade7',before_bytes=134,after_sha256='1d2f61832b2596b0046cb82cf3634609ea866098d097a83fac27c35272ac726a',after_bytes=260835655)})]:
 with (R/'inputs'/name).open('x') as f:json.dump(data,f,indent=2,sort_keys=True);f.write('\n')
# Direct descriptive read only: no lifecycle, eligibility, or lock operations.
sys.path.insert(0,str(R/'scripts'))
from continuation import terminal
with (R/'inputs/r8-unapproved-description.json').open('x') as f:json.dump(terminal(plan,describe=True),f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps(dict(staged=str(R),approval_created=False,integration=False,cache_lineage='BLOCKED'),indent=2))
'''
s='FILES='+repr(files)+'\nEVIDENCE='+repr(evidence)+'\n'+s
print(remote.run(s))
