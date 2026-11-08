#!/usr/bin/env python3
"""Apply the patch only to an isolated temporary copy under this spike."""
import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent/'2026-11-06-asus-android17-build-continuation'
receipts=json.loads((ROOT/'evidence/integration-receipts.json').read_text())
for name,receipt in receipts.items():
    p=BASE/name
    if 'before_exists' in receipt:
        assert p.exists()==receipt['before_exists']
        data=p.read_bytes() if p.exists() else b'';expected=receipt['before_sha256']
    else:data=p.read_bytes();expected=receipt['unchanged_dependency_sha256']
    assert hashlib.sha256(data).hexdigest()==expected, 'Source changed: '+name
with tempfile.TemporaryDirectory(dir=ROOT/'tests',prefix='integration-') as directory:
    tree=Path(directory)
    for name in receipts:
        p=BASE/name
        if p.exists():
            target=tree/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    proc=subprocess.run(['/usr/bin/patch','-p1','--batch','-i',str((ROOT/'evidence/replacement.patch').resolve())],cwd=tree,text=True,capture_output=True)
    assert proc.returncode==0,proc.stdout+proc.stderr
    source=ROOT/'artifacts/Image.gz-dtb-combined-r1';out=tree/'artifacts/fixture'
    proc=subprocess.run([sys.executable,str(tree/'scripts/package_full_boot.py'),'--aosp-boot',str(source/'NONBOOTABLE-SYNTHETIC-AOSP-input.img'),'--build-report',str(source/'input-report.json'),'--kernel',str(BASE/'artifacts/Image.gz-dtb-combined-r1'),'--out',str(out),'--mode','SYNTHETIC_FIXTURE'],text=True,capture_output=True)
    assert proc.returncode==0,proc.stderr
    expected=json.loads((source/'manifest.json').read_text())['image_sha256']
    got=hashlib.sha256((out/'NONBOOTABLE-SYNTHETIC-full-BOOT.img').read_bytes()).hexdigest()
    assert got==expected
    result={'patch_applied_to':'temporary isolated copy under tests (removed after test)','active_sources_changed':False,'exit_code':proc.returncode,'fixture_image_sha256':got,'matches_standalone':True}
(ROOT/'evidence/integration-patch-test.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS patch application and deterministic output with original probe helpers; active target unchanged')
