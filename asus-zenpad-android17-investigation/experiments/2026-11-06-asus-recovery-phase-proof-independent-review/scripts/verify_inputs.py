from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(__file__).resolve().parents[1];base=R.parent
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
orig=json.loads((R/'evidence/original-sha256.json').read_text())
assert all(h(R/'snapshot'/n)==v for n,v in orig.items())
assert all(h(base/'2026-11-06-asus-recovery-phase-proof'/n)==v for n,v in orig.items())
receipts=json.loads((R/'snapshot/evidence/frozen-input-receipts.json').read_text())
verified={}
for name,rec in receipts.items():
 # Only exact recovery source/policy/proxy/frozen public artifacts; no private files.
 if name.startswith('2026-11-06-asus-stock-only-ram-rescue-build/') or name=='2026-11-06-asus-android17-target-rescue/source/proxy.c':
  p=base/name;assert p.stat().st_size==rec['bytes'];assert h(p)==rec['sha256'];verified[name]=rec
source=R/'snapshot/source';baseline=R/'snapshot/baseline'
for n in ['common.h','sha256.h','handoff.h']:assert (source/n).read_bytes()==(baseline/n).read_bytes()
assert (R/'fixture/source/rescue.c').read_bytes()==(source/'rescue.c').read_bytes()
assert (R/'fixture/source/recovery_phase.h').read_bytes()==(source/'recovery_phase.h').read_bytes()
# Independently apply the patch to a disposable original source copy, preserving original paths.
patched=R/'evidence/independent-patch'
if patched.exists():shutil.rmtree(patched)
(patched/'source').mkdir(parents=True)
shutil.copyfile(baseline/'rescue.c',patched/'source/rescue.c')
p=subprocess.run(['patch','-p1','-i',str(R/'snapshot/future-source.patch')],cwd=patched,capture_output=True,text=True)
assert p.returncode==0,p.stderr
assert (patched/'source/rescue.c').read_bytes()==(source/'rescue.c').read_bytes()
assert (patched/'source/recovery_phase.h').read_bytes()==(source/'recovery_phase.h').read_bytes()
# Extracted exact init and labels match frozen core inventory. No key entry bytes read.
inv=json.loads((base/'2026-11-06-asus-stock-only-ram-rescue-build/artifacts/core-entries.json').read_text())
for n in ['init.rc','ueventd.rc','default.prop']:assert h(R/'snapshot/context'/n)==inv[n]['sha256']
assert inv['system/bin/sh']['sha256']==inv['sbin/rescue-proxy']['sha256']
assert inv['sbin/ueventd']['mode']&0o170000==0o120000
assert h(R/'snapshot/context/restore-sepolicy')==inv['sepolicy']['sha256']
assert h(R/'snapshot/context/file_contexts.bin')==inv['file_contexts.bin']['sha256']
(R/'evidence/independent-input-verification.json').write_text(json.dumps(dict(passed=True,snapshot_files=len(orig),originals_unchanged=True,patch_applies_exactly=True,unchanged_supporting_headers=True,core_inventory_matched_configs=True,frozen_receipts_verified=verified),indent=2)+'\n')
print('Preserved snapshot/original files:',len(orig),'; independently verified frozen receipts:',len(verified),'; exact patch/header checks: pass')
