"""Hash/structural checks only. No imports or execution of target source."""
from pathlib import Path
import hashlib
import json
import struct

ROOT=Path(__file__).resolve().parents[2]
OWN=Path(__file__).resolve().parents[1]
STOCK=ROOT/'2026-11-06-asus-stock-only-ram-rescue-build'
DESIGN=ROOT/'2026-11-06-asus-final5role-terminal-restore-contract'
PHASE=ROOT/'2026-11-06-asus-recovery-phase-proof'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

pins=json.loads((PHASE/'evidence/frozen-input-receipts.json').read_text())
frozen=[]
for path,pin in pins.items():
    if not path.startswith(STOCK.name+'/'): continue
    p=ROOT/path
    actual=dict(bytes=p.stat().st_size,sha256=sha(p))
    frozen.append(dict(path=path,expected=pin,actual=actual,passed=actual==pin))
assert all(row['passed'] for row in frozen)

image=STOCK/'artifacts/candidate/UNAPPROVED-STOCK-ONLY.img'
h=hashlib.sha256()
with image.open('rb') as f:
    for chunk in iter(lambda:f.read(1024**2),b''):h.update(chunk)
assert h.hexdigest()=='5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f'
# Hash the documented compact-image/zero-tail representation in small blocks.
# This never writes or materializes a new image/full-p10 file.
left=16740352-image.stat().st_size;zeros=bytes(65536)
while left:
    n=min(left,len(zeros));h.update(zeros[:n]);left-=n
assert h.hexdigest()=='3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a'

manifest=(STOCK/'artifacts/original-stock.manifest').read_bytes()
assert len(manifest)==115288 and hashlib.sha256(manifest).hexdigest()=='605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47'
count=struct.unpack_from('<I',manifest,12)[0];assert count==2
off=112;original=[]
for i in range(count):
    role,part,size=struct.unpack_from('<IIQ',manifest,off)
    full=manifest[off+16:off+48].hex();chunks=struct.unpack_from('<I',manifest,off+48)[0]
    table=manifest[off+52:off+52+chunks*32]
    original.append(dict(role=role,part=part,size=size,full=full,count=chunks,table_sha256=hashlib.sha256(table).hexdigest()))
    off+=52+chunks*32
assert off==len(manifest)

av=json.loads((OWN/'evidence/effective-policy.json').read_text())['rows']
previous={}
for line in (PHASE/'evidence/policy-reachability.txt').read_text().splitlines():
    src,tgt,cls,*perms=line.split();previous[(src,tgt,cls)]=sorted(perms)
assert len(previous)==144
for row in av:
    src=row['source'].split(':')[2];tgt=row['target'].split(':')[2]
    assert previous[(src,tgt,row['cls'])]==row['allowed']

extra_paths=[
    PHASE/'README.md',PHASE/'REPORT.md',PHASE/'PARENT-REVIEW-RESOLUTION.md',
    PHASE/'source/recovery_phase.h',PHASE/'source/rescue.c',PHASE/'future-source.patch',
    PHASE/'tests/policy_reachability.c',PHASE/'evidence/policy-reachability.txt',
    PHASE/'context/init.rc',PHASE/'context/default.prop',PHASE/'context/ueventd.rc',
    ROOT/'2026-11-06-asus-android17-target-rescue/source/proxy.c',
    ROOT/'2026-11-06-asus-android17-target-rescue/source/policy_build.c',
    ROOT/'2026-11-06-asus-stock-rescue-commissioning-artifact/source/package.py',
    ROOT/'2026-11-06-asus-ram-original-recovery-restorer/scripts/prepare.py',
    STOCK/'artifacts/base-policy',STOCK/'artifacts/file_contexts.bin',STOCK/'artifacts/file_contexts',
]
extras={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in extra_paths}
assert sha(STOCK/'artifacts/base-policy')=='189c477ac73ecb161a6527f7f98a6fec76a913b0d5cf8d11591d440dc79af842'
assert not list(DESIGN.rglob('terminal_manifest_binding.h'))
patch=(DESIGN/'proposal/terminal-profile.patch.txt').read_text()
assert '+ if(!terminal_profile_matches()||uncertain_image!=-1||identity()||verify_image(0)||verify_image(1))return -1;' in patch
assert '+ if(ram_only()||load_manifest()||!terminal_profile_matches())return 84;' in patch
assert '+ return image_count==5&&!memcmp(manifest_id,terminal_manifest_sha,32);' in patch
result=dict(frozen_receipts_checked=len(frozen),frozen_receipts=frozen,
            compact_image_sha256=sha(image),logical_padded_p10_sha256=h.hexdigest(),
            padded_p10_file_written=False,original_manifest=original,
            prior_144_effective_rows_match_fresh_query=True,additional_public_inputs=extras,
            generated_manifest_header_absent=True,review_patch_structural_checks=True,
            future_manifest_bytes=112+5*52+32*(3580+16+3580+16+10807),
            data_last_chunk_bytes=11331268096-10806*1048576,
            both_original_pair_passes_bytes=2*(3753902080+16740352),
            final_p10_stage_bytes=16740352-15*1048576)
(OWN/'evidence/review-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('frozen_receipts','original_manifest','additional_public_inputs')}))
