from pathlib import Path
import hashlib,json,os,resource
R=Path(__file__).resolve().parents[1]; O=Path('/srv/android/2026-11-06-asus-stock-only-ram-rescue-build')
assert str(R)=='/srv/android/2026-11-06-stock-review'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins=json.loads((O/'inputs/remote-original-pins.json').read_text());old=Path('/srv/android/2026-11-06-asus-ram-original-recovery-restorer')
for name,pin in pins.items():assert sha(old/name)==pin,name
tools=json.loads((O/'evidence/toolchain.json').read_text())
for name,item in tools.items():assert sha(Path(item['path']))==item['sha256'],name
before=json.loads((R/'evidence/remote-inputs-before.json').read_text())
after={str(p.relative_to(O)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(O.rglob('*')) if p.is_file()}
assert before==after
result=dict(passed=True,old_public_inputs_verified=len(pins),original_build_fixture_files_unchanged=len(after),recorded_toolchain_files_verified=len(tools),review_fixture=str(R),device_operations=0,cloud_lifecycle_operations=0)
(R/'evidence/final-remote-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
