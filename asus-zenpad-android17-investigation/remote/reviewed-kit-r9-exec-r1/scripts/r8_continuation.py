"""Incremental r8: exact terminal r7, two source writes, no baseline replay."""
import datetime
from pathlib import Path
import re
import shutil
from ancestor_continuation import sensor_delta

R7_SEAL='9287a07d243a9d70abefa0102de160d88af712a574c7fab6032ce9b36920f617'
LOG='e18314db5121a830f0f000f8c40616e2377312a804e22e477ae20030472bdc61'
END='2026-11-06T23:02:58.864381+00:00'
WPA='connectivity/src/driver_cmd_p00a.c'
CONTEXT='sepolicy/vendor/file_contexts'
INCLUDES=b'#include "includes.h"\n#include "common.h"\n#include "driver_nl80211.h"\n#include "linux_ioctl.h"\n'
BOUNDARY=(b'/* Upstream disabled-feature inline stubs have unused parameters. Keep the\n'
          b' * exception at this include boundary; adapter code retains -Wextra -Werror. */\n'
          b'#pragma clang diagnostic push\n#pragma clang diagnostic ignored "-Wunused-parameter"\n'+INCLUDES+
          b'#pragma clang diagnostic pop\n')
ZRAM=b'/dev/block/zram0    u:object_r:swap_block_device:s0\n'

def deltas(plan):
    from integrate import need,read,sha
    candidate=Path(plan['run_root'])/'inputs/lmkd-functional/vendor-file-contexts.additions'
    entries=[l for l in candidate.read_bytes().splitlines(keepends=True) if l.strip() and not l.lstrip().startswith(b'#')]
    need(entries==[ZRAM], 'Memory handoff context selection changed')
    rows=read(plan['r8_delta'])
    need(set(rows)=={WPA,CONTEXT},'r8 must contain exactly WPA source and zRAM context deltas')
    for rel,row in rows.items():
        before=Path(plan['run_root'])/'inputs/r8-preimages'/rel
        after=Path(plan['staging'])/'product-device'/rel
        need(set(row)=={'before','after'} and sha(before)==row['before'] and sha(after)==row['after'],'r8 delta pins mismatch: '+rel)
        b=before.read_bytes()
        if rel==WPA:
            need(b.count(INCLUDES)==1 and after.read_bytes()==b.replace(INCLUDES,BOUNDARY),'WPA must change only the upstream include diagnostic boundary')
        else:
            need(b.endswith(b'\n') and b'/dev/block/zram0' not in b and after.read_bytes()==b+ZRAM,'zRAM must add only the exact swap_block_device context')
    return rows

def continuation_inputs(plan):
    from integrate import need,read,sha,verify_pins,manifest
    from ancestor_continuation import continuation_inputs as ancestor
    prior=Path(plan['r7_kit'])
    need(verify_pins(prior)==R7_SEAL,'r7 kit drift')
    ancestor(read(prior/'inputs/plan.json'))
    rows=deltas(plan)
    pins=read(plan['r7_preservation'])
    for group in ['attempt_files','logs','frozen_evidence']:
        for p,row in pins[group].items():
            need(Path(p).is_file() and not Path(p).is_symlink() and sha(p)==row['sha256'] and Path(p).stat().st_size==row['bytes'],'r7 preserved evidence drift: '+p)
    need({str(p) for p in (prior/'attempt').rglob('*') if p.is_file() or p.is_symlink()}==set(pins['attempt_files']),'r7 attempt file set drift')
    need({str(p) for p in Path(plan['logs']).glob('full-build-r7.*')}==set(pins['logs']),'r7 log file set drift')
    need(read(plan['r7_integration'])==read(prior/'attempt/integration.json'),'r7 integration receipt drift')
    expected=read(plan['r7_staged_receipt'])
    need(expected==read(prior/'inputs/STAGED.json'),'r7 staged receipt drift')
    for rel,row in rows.items():
        need(expected['product_after'][rel]=={'sha256':row['before']},'r7 source preimage drift')
        expected['product_after'][rel]={'sha256':row['after']}
    need(read(plan['staged_receipt'])==expected,'r8 staged receipt has unrelated changes')
    old_manifest=read(plan['r7_staging_manifest']);expected_stage=dict(old_manifest)
    for rel,row in rows.items():expected_stage['product-device/'+rel]={'sha256':row['after']}
    expected_stage['STAGED.json']={'sha256':sha(plan['staged_receipt'])}
    need(manifest(plan['staging'])==read(plan['staging_manifest'])==expected_stage,'r8 staging has unrelated changes')
    need(read(plan['sensor_receipt'])==read(prior/'inputs/sensor-selection.json'),'Sensor source selection changed')
    need(read(plan['r7_integration'])['product_after']==read(plan['r7_staged_receipt'])['product_after'],'r7 integration/source mismatch')
    return rows

def terminal(plan,review=None,describe=False):
    from integrate import need,sha,read
    prefix=Path(plan['logs'])/'full-build-r7'
    paths={n:Path(str(prefix)+'.'+n) for n in ['started','finished','exit-code','log']}
    need(all(p.is_file() and not p.is_symlink() and p.stat().st_size for p in paths.values()),'r7 lacks actual terminal records')
    need(paths['exit-code'].read_text().strip()=='1' and not Path(str(prefix)+'.complete').exists(),'Unexpected r7 result')
    start=datetime.datetime.fromisoformat(paths['started'].read_text().strip());end=datetime.datetime.fromisoformat(paths['finished'].read_text().strip())
    need(start.tzinfo and end.tzinfo and start<=end<=datetime.datetime.now(datetime.timezone.utc) and end.isoformat()==END,'r7 terminal identity changed')
    need(sha(paths['log'])==LOG,'r7 terminal log changed')
    failed=Path(plan['r7_kit'])/'attempt/FAILED.json'
    need(failed.is_file() and read(failed).get('retry_allowed') is False,'Preserve actual r7 FAILED.json')
    pins=read(plan['r7_preservation'])
    for group in ['attempt_files','logs','frozen_evidence']:
        for p,row in pins[group].items():
            need(sha(p)==row['sha256'] and Path(p).stat().st_size==row['bytes'],'r7 terminal preservation drift: '+p)
    need({str(p) for p in (Path(plan['r7_kit'])/'attempt').rglob('*') if p.is_file() or p.is_symlink()}==set(pins['attempt_files']),'r7 attempt file set drift')
    need({str(p) for p in Path(plan['logs']).glob('full-build-r7.*')}==set(pins['logs']),'r7 evidence file set drift')
    observed=dict(revision='r7',exit_code=1,terminal_kind='ACTUAL_BUILD_FAILURE',finished=END,terminal_log_sha256=LOG,r7_kit_pins_sha256=R7_SEAL,preservation=pins,
        images={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(Path(plan['product_out']).glob('*.img'))})
    if describe:return dict(status='TERMINAL_FAILED_REQUIRES_PARENT_REVIEW',review_template=dict(reviewed_by_parent=False,reason='',prior=observed))
    need(review is not None,'Actual terminal r7 requires hash-bound parent failure acceptance')
    path,digest=review
    need(Path(path).resolve().is_relative_to(Path(plan['run_root'])/'parent-review'),'Parent acceptance must be under own parent-review')
    need(re.fullmatch('[0-9a-f]{64}',digest or '') and not Path(path).is_symlink() and sha(path)==digest,'Parent acceptance hash mismatch')
    accepted=read(path)
    need(set(accepted)=={'reviewed_by_parent','reason','prior'} and accepted['reviewed_by_parent'] is True and isinstance(accepted['reason'],str) and accepted['reason'].strip(),'r7 failure not accepted by parent')
    need(accepted['prior']==observed,'r7 evidence changed since parent review')
    return dict(terminal_kind='FAILED_REVIEWED_FOR_NEW_REVISION',observed=observed,parent_review_sha256=digest)

def preserve(plan,attempt,previous):
    from integrate import need,write,item,sha,safe,read
    before=attempt/'before';before.mkdir();backups={}
    for rel,row in deltas(plan).items():
        src=safe(plan['device'],rel);dst=before/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        need(item(src)=={'sha256':row['before']},'r8 preimage drift before preservation')
        shutil.copy2(src,dst);need(item(dst)==item(src),'Source preservation mismatch');backups[rel]=dict(path=str(src),backup=str(dst),sha256=row['before'])
    logs=before/'logs';logs.mkdir()
    for p,row in read(plan['r7_preservation'])['logs'].items():
        dst=logs/Path(p).name;shutil.copy2(p,dst);need(sha(dst)==row['sha256'],'r7 log preservation mismatch')
    write(attempt/'preservation.json',dict(source_preimages=backups,r7_failure=previous,prior_attempts_preserved_in_place=[plan['prior_attempt'],str(Path(plan['r7_kit'])/'attempt')],prior_preservation_pins_sha256=sha(plan['r7_preservation']),cache_and_images_preserved_in_place=True))

def apply(plan,attempt):
    from integrate import need,read,write,sha,manifest,safe,copy_exact,verify_integrated
    rows=deltas(plan)
    need(manifest(plan['device'])==read(plan['r7_staged_receipt'])['product_after'],'Already-integrated r7 preimage changed')
    for rel,row in rows.items():copy_exact(safe(Path(plan['staging'])/'product-device',rel),safe(plan['device'],rel),{'sha256':row['after']})
    write(attempt/'postimages.json',verify_integrated(plan,baseline=True))
    record=read(plan['r7_integration']);record.update(product_after=manifest(plan['device']),staged_receipt_sha256=sha(plan['staged_receipt']),sensor_receipt_sha256=sha(plan['sensor_receipt']),prior_integration_receipt_sha256=sha(plan['r7_integration']),r8_delta_sha256=sha(plan['r8_delta']),sensor_delta_sha256=sha(plan['sensor_delta']),source_writes=[dict(path=str(safe(plan['device'],r)),**v) for r,v in rows.items()],preservation_receipt_sha256=sha(attempt/'preservation.json'),active_source_postimages_sha256=sha(attempt/'postimages.json'),prior_kit_pins_sha256=R7_SEAL,revision='r8')
    write(attempt/'integration.json',record)
