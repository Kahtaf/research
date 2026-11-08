from pathlib import Path
import hashlib,json,sys,difflib
R=Path(__file__).resolve().parents[1];old=R.parent/'2026-11-06-asus-stock-only-ram-rescue-build'
H=lambda b:hashlib.sha256(b).hexdigest()
paths=[old/'source'/p.name for p in (R/'baseline').iterdir()]
paths += [old/p for p in ['HANDOFF.md','HANDOFF.json','source/host.py','source/generated_host_binding.py','source/policy_audit.c','artifacts/p10-restore','artifacts/os-rescue','artifacts/rescue-proxy','artifacts/restore-sepolicy','artifacts/file_contexts.bin','artifacts/original-stock.manifest','artifacts/core.cpio.gz','artifacts/core-entries.json','artifacts/candidate/UNAPPROVED-STOCK-ONLY.img','artifacts/candidate/session-contract.UNAPPROVED.json']]
paths += [R.parent/'2026-11-06-asus-rescue-independent-review'/p for p in ['REPORT.md','HANDOFF.json']]
paths += [R.parent/'2026-11-06-asus-android17-target-rescue'/p for p in ['REPORT.md','source/rescue.c','source/common.h','source/proxy.c','source/policy_build.c','source/init.rc','source/ueventd.rc','source/default.prop','source/libsepol-android-7.1.2_r39.tar.gz']]
rows={str(p.relative_to(R.parent)):dict(bytes=p.stat().st_size,sha256=H(p.read_bytes())) for p in paths}
for p in (R/'baseline').iterdir():assert p.read_bytes()==(old/'source'/p.name).read_bytes(),p
assert rows[str((old/'artifacts/candidate/UNAPPROVED-STOCK-ONLY.img').relative_to(R.parent))]['sha256']=='5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f'
assert rows[str((old/'artifacts/original-stock.manifest').relative_to(R.parent))]['sha256']=='605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47'
p=R/'evidence/frozen-input-receipts.json'
if p.exists():assert rows==json.loads(p.read_text()),'frozen input changed'
else:p.write_text(json.dumps(rows,indent=2)+'\n')
post={str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=H(p.read_bytes())) for p in sorted((R/'source').iterdir())}
(R/'evidence/proposed-source-receipts.json').write_text(json.dumps(post,indent=2)+'\n')
for name in ['common.h','sha256.h','handoff.h']:assert (R/'source'/name).read_bytes()==(R/'baseline'/name).read_bytes()
a=(R/'baseline/rescue.c').read_text().splitlines(True);b=(R/'source/rescue.c').read_text().splitlines(True)
patch=''.join(difflib.unified_diff(a,b,fromfile='a/source/rescue.c',tofile='b/source/rescue.c'))
new=(R/'source/recovery_phase.h').read_text().splitlines(True)
patch+=''.join(difflib.unified_diff([],new,fromfile='/dev/null',tofile='b/source/recovery_phase.h'))
(R/'future-source.patch').write_text(patch)
print(json.dumps(dict(frozen_inputs_unchanged=len(rows),baseline_matches=True,production_delta=['rescue.c','recovery_phase.h'])))
