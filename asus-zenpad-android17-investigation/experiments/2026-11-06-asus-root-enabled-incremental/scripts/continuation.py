"""Exact r9 artifact-only continuation from integrated terminal r8."""
import datetime
from pathlib import Path
import re
import shutil
from ancestor_continuation import sensor_delta
from artifact import REL,OID,SIZE,BEFORE,admit,check_preimage,materialize

R8_SEAL='f55aedf8ac9d2a513e3663230db0b9d802e72b5df512fc0db6b3714331a7efa4'
LOG='dde9978375f6e34e8b09676a2cb3245e866486ee254cf5405204b85893b37c38'
FAILED_COMMAND='f942dd841d60dd53582d6d0a8ab403b4095bb8000947d47cfd4bc94fc0b7bbe4'
END='2026-11-06T23:48:28.389783+00:00'

def preservation(plan):
    from integrate import need,read,sha
    prior=Path(plan['r8_kit']);pins=read(plan['r8_preservation'])
    for group in ['attempt_files','logs']:
        for path,row in pins[group].items():
            p=Path(path);need(not p.is_symlink() and p.is_file() and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'r8 preserved evidence drift: '+path)
    need({str(p) for p in (prior/'attempt').rglob('*') if p.is_file() or p.is_symlink()}==set(pins['attempt_files']),'r8 attempt set drift')
    need({str(p) for p in Path(plan['logs']).glob('full-build-r8.*')}==set(pins['logs']),'r8 log set drift')
    return pins

def deltas(plan):
    from integrate import need,read
    rows=read(plan['r9_delta'])
    need(rows=={REL:dict(before_sha256=BEFORE,before_bytes=134,after_sha256=OID,after_bytes=SIZE)},'Artifact source scope changed')
    return rows

def continuation_inputs(plan):
    from integrate import need,read,sha,verify_pins,manifest
    from r8_continuation import continuation_inputs as inherited
    deltas(plan)
    inherited(plan)
    prior=Path(plan['r8_kit'])
    need(verify_pins(prior)==R8_SEAL,'r8 seal drift')
    preservation(plan)
    need(read(plan['r8_integration'])==read(prior/'attempt/integration.json'),'r8 integration drift')
    need(manifest(plan['device']) == read('/srv/android/asus-root-enabled-incremental-r1/inputs/expected-product.json'), 'Exact root-enabled product manifest drift')
    admit(plan['artifact_staging'])
    return read(plan['r9_delta'])

def terminal(plan,review=None,describe=False):
    from integrate import need,read,sha
    prefix=Path(plan['logs'])/'full-build-r8'
    paths={n:Path(str(prefix)+'.'+n) for n in ['started','finished','exit-code','log']}
    need(all(p.is_file() and not p.is_symlink() and p.stat().st_size for p in paths.values()),'Actual r8 terminal missing')
    need(paths['exit-code'].read_text().strip()=='1' and not Path(str(prefix)+'.complete').exists(),'r8 result changed')
    start=datetime.datetime.fromisoformat(paths['started'].read_text().strip());end=datetime.datetime.fromisoformat(paths['finished'].read_text().strip())
    need(start.tzinfo and end.tzinfo and start<=end<=datetime.datetime.now(datetime.timezone.utc) and end.isoformat()==END,'r8 terminal identity changed')
    need(sha(paths['log'])==LOG,'r8 terminal log drift')
    prior=Path(plan['r8_kit'])
    need(read(prior/'attempt/FAILED.json').get('retry_allowed') is False,'Actual r8 failure must remain')
    need(sha(prior/'attempt/native-evidence/bootimage/siso_failed_commands.sh')==FAILED_COMMAND,'Frozen actual failed command drift')
    observed=dict(revision='r8',exit_code=1,terminal_kind='ACTUAL_BUILD_FAILURE',finished=END,terminal_log_sha256=LOG,r8_kit_pins_sha256=R8_SEAL,preservation=preservation(plan),images={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(Path(plan['product_out']).glob('*.img'))})
    if describe:return dict(status='TERMINAL_FAILED_REQUIRES_PARENT_REVIEW',review_template=dict(reviewed_by_parent=False,reason='',prior=observed))
    need(review is not None,'Parent-authored r8 failure acceptance required')
    path,digest=review;p=Path(path)
    need(p.resolve().is_relative_to(Path(plan['run_root'])/'parent-review'),'Parent acceptance outside own review directory')
    need(re.fullmatch('[0-9a-f]{64}',digest or '') and not p.is_symlink() and sha(p)==digest,'Parent review hash drift')
    accepted=read(p)
    need(set(accepted)=={'reviewed_by_parent','reason','prior'} and accepted['reviewed_by_parent'] is True and isinstance(accepted['reason'],str) and accepted['reason'].strip(),'Unapproved parent acceptance')
    need(accepted['prior']==observed,'r8 evidence changed since parent review')
    return dict(terminal_kind='FAILED_REVIEWED_FOR_NEW_REVISION',observed=observed,parent_review_sha256=digest)

def preserve(plan,attempt,previous):
    from integrate import write,sha,need
    before=attempt/'before';before.mkdir()
    dst=before/REL;dst.parent.mkdir(parents=True)
    src=Path(plan['aosp'])/REL;check_preimage(src)
    with src.open('rb') as inp,dst.open('xb') as out:shutil.copyfileobj(inp,out)
    check_preimage(dst)
    logs=before/'logs';logs.mkdir()
    for p,row in preservation(plan)['logs'].items():
        with Path(p).open('rb') as inp,(logs/Path(p).name).open('xb') as out:shutil.copyfileobj(inp,out,1048576)
        need(sha(logs/Path(p).name)==row['sha256'],'r8 copied log drift')
    write(attempt/'preservation.json',dict(source_preimages={REL:dict(path=str(src),backup=str(dst),sha256=BEFORE)},r8_failure=previous,prior_attempts_preserved_in_place=[str(Path(plan['r8_kit'])/'attempt'),plan['prior_attempt']],cache_and_images_preserved_in_place=True))

def apply(plan,attempt):
    from integrate import read,write,verify_integrated,sha
    # The parent supervisor rechecks all inherited source before calling this.
    materialize(plan['artifact_staging'],Path(plan['aosp'])/REL,attempt/'atomic-pointer-backup')
    post=verify_integrated(plan,baseline=True);post['webview']=admit(Path(plan['aosp'])/REL)
    write(attempt/'postimages.json',post)
    record=read(plan['r8_integration']);record.update(revision='r9',prior_integration_receipt_sha256=sha(plan['r8_integration']),r9_delta_sha256=sha(plan['r9_delta']),source_writes=[dict(path=str(Path(plan['aosp'])/REL),before=BEFORE,after=OID)],preservation_receipt_sha256=sha(attempt/'preservation.json'),active_source_postimages_sha256=sha(attempt/'postimages.json'),prior_kit_pins_sha256=R8_SEAL)
    write(attempt/'integration.json',record)
