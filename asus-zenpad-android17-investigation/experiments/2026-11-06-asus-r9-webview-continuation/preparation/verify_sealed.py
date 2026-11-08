from pathlib import Path
import remote,json
s=r'''
from pathlib import Path
import json,sys,subprocess,hashlib
R=Path('/srv/android/asus-reviewed-build-kit/r9');F=Path('/srv/android/asus-reviewed-build-kit/r9-fixtures');M=Path('/srv/android/asus-reviewed-build-kit/r9-webview-input-milestone-v1');sys.path.insert(0,str(R/'scripts'))
from integrate import verify_pins
from artifact import REL,check_preimage
seal=verify_pins(R);assert seal=='7850aa14d465cfa7cb061ed6cde5fe23c28041a5b4f5e9f7fd8c7d4d62956b5c'
# Default PLAN_ONLY is proven to reject before its process/lock/source paths.
p=subprocess.run(['python3','-B',str(R/'scripts/integrate.py')],cwd=F,capture_output=True,text=True,timeout=60)
assert p.returncode==20 and json.loads(p.stdout)['status']=='REFUSED' and 'CACHE_LINEAGE_INCOMPLETE' in p.stdout
assert not (R/'attempt').exists() and not (R/'parent-review').exists()
check_preimage(Path('/srv/android/lineage24')/REL)
for rel in json.loads((R/'inputs/kit-pins.json').read_text()):(R/rel).chmod(0o444)
(R/'inputs/kit-pins.json').chmod(0o444);(R/'kit-seal.json').chmod(0o444)
assert verify_pins(R)==seal
milestone_pin=hashlib.sha256((M/'pins.json').read_bytes()).hexdigest();assert milestone_pin=='3e6ca30a3074cdd7f19dd522111c52fadbfdb311a3aa16fd23563c9011e35437'
r=dict(kit_pins_sha256=seal,pins_verified=True,pinned_files_readonly=True,plan_only_exit=p.returncode,plan_only_result=json.loads(p.stdout),milestone_pins_sha256=milestone_pin,r9_attempt_absent=True,parent_review_absent=True,active_webview_original_pointer=True,cache_admitted=False,build_started=False,physical_go=False)
with (F/'post-seal-verification.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/post-seal-verification.json').write_text(r);print(r)
