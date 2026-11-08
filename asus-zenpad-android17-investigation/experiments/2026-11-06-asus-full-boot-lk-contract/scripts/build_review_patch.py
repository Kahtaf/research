#!/usr/bin/env python3
"""Generate review artifacts only; never modify the integration target."""
import difflib,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent/'2026-11-06-asus-android17-build-continuation'
changes=['scripts/package_full_boot.py','scripts/boot_memory.py','scripts/lk_contract.py']
patch=[];receipts={}
for name in changes:
    before=(BASE/name).read_bytes() if (BASE/name).exists() else b''
    after=(ROOT/name).read_bytes()
    saved=ROOT/'source/baseline'/name;saved.parent.mkdir(parents=True,exist_ok=True)
    if saved.exists():assert saved.read_bytes()==before,'Integration target changed since snapshot'
    else:saved.write_bytes(before)
    receipts[name]={'before_sha256':hashlib.sha256(before).hexdigest(),'before_exists':(BASE/name).exists(),'after_sha256':hashlib.sha256(after).hexdigest()}
    patch+=difflib.unified_diff(before.decode().splitlines(keepends=True),after.decode().splitlines(keepends=True),fromfile='a/'+name if before else '/dev/null',tofile='b/'+name)
for name in ['probe/bootformat.py','probe/fdt.py','inputs/stock-kernel-wrapper.bin','inputs/stock-ramdisk-wrapper.bin','evidence/stock-wrapper-provenance.json']:
    data=(BASE/name).read_bytes();receipts[name]={'unchanged_dependency_sha256':hashlib.sha256(data).hexdigest()}
(ROOT/'evidence/replacement.patch').write_text(''.join(patch))
(ROOT/'evidence/integration-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
print('Generated isolated replacement.patch; no integration target writes')
