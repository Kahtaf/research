#!/usr/bin/env python3
"""Apply the reviewed graphics-only profile, while no build is running."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path('/srv/android/asus-device-product')
TREE = Path('/srv/android/lineage24')
BUNDLE = Path(__file__).parent
backup = ROOT / 'before-graphics-profile-r5'
assert not backup.exists(), 'Profile already attempted; inspect evidence before proceeding'
active = subprocess.run(['pgrep', '-af', r'out/soong_ui --build-mode|prebuilts/siso/linux-x86/siso|/ninja |/soong_build '], capture_output=True, text=True)
assert not active.stdout.strip(), 'A platform build is active: ' + active.stdout
source = TREE / 'system/linkerconfig'
manifest = json.loads((BUNDLE / 'source-manifest.json').read_text())
for relative,row in manifest.items():
    path = source / relative
    if row['before_sha256'] is None:
        assert not path.exists(), path
    else:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['before_sha256'], path
subprocess.run(['git','apply','--check',str(BUNDLE/'linkerconfig.patch')], cwd=source, check=True)
backup.mkdir()
for relative,row in manifest.items():
    if row['before_sha256']:
        out = backup / 'system/linkerconfig' / relative
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source/relative,out)
for name,relative in [('device.mk','device/asus/p00a/device.mk'),('lights.Android.bp','device/asus/p00a/lights/Android.bp')]:
    path = TREE / relative
    out = backup / relative
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path,out)
    shutil.copyfile(BUNDLE/name,path)
subprocess.run(['git','apply',str(BUNDLE/'linkerconfig.patch')], cwd=source, check=True)
for relative,row in manifest.items():
    assert hashlib.sha256((source/relative).read_bytes()).hexdigest() == row['after_sha256'], relative
(ROOT / 'logs/graphics-profile-r5.json').write_text(json.dumps(dict(exit_status=0,
    source_before_after=manifest, source_pin=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()), indent=2)+'\n')
print('Verified and deployed graphics profile r5; previous platform/product sources preserved')
