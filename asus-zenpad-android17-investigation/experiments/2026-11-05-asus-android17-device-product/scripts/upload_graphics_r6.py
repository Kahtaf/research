#!/usr/bin/env python3
"""Preserve r5 and deploy only its test include-order correction for r6."""
from pathlib import Path
import io,json,subprocess,tarfile,difflib,hashlib
from graphics_remote import SSH
ROOT=Path(__file__).resolve().parents[1]
rel='contents/tests/configuration/p00a_legacy_graphics_test.cc'
old=subprocess.check_output(SSH+['cat /srv/android/lineage24/system/linkerconfig/'+rel])
new=old.decode().replace('#include "mockenv.h"','#include "linkerconfig/apex.h"\n#include "mockenv.h"')
assert old.decode().count('#include "mockenv.h"')==1
assert hashlib.sha256(old).hexdigest()==json.loads((ROOT/'compatibility/graphics-r5/source-manifest.json').read_text())[rel]['after_sha256']
assert hashlib.sha256(new.encode()).hexdigest()==json.loads((ROOT/'compatibility/graphics-r6/source-manifest.json').read_text())[rel]['after_sha256']
patch=''.join(difflib.unified_diff(old.decode().splitlines(True),new.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
(ROOT/'compatibility/graphics-r6/from-r5.patch').write_text(patch)
bundle=io.BytesIO()
with tarfile.open(fileobj=bundle,mode='w') as t:
 for name in ['build_graphics.sh','capture_graphics_revision.py','run_graphics_revision.py']:
  t.add(ROOT/'scripts'/name,arcname=name)
 for name in ['linkerconfig.patch','source-manifest.json','from-r5.patch']:
  t.add(ROOT/'compatibility/graphics-r6'/name,arcname=name)
subprocess.run(SSH+['mkdir /srv/android/asus-device-product/revisions/r6 && tar -xf - -C /srv/android/asus-device-product/revisions/r6'],input=bundle.getvalue(),check=True)
script='''from pathlib import Path
import hashlib,json,shutil,subprocess
root=Path('/srv/android/asus-device-product'); tree=Path('/srv/android/lineage24')
active=subprocess.run(['pgrep','-af',r'out/soong_ui --build-mode|prebuilts/siso/linux-x86/siso|/ninja |/soong_build '],capture_output=True,text=True)
assert not active.stdout.strip(),active.stdout
assert json.loads((root/'logs/graphics-build-r5-job.json').read_text())['status']=='failed'
manifest=json.loads((tree/'vendor/asus/p00a/ready-manifest.json').read_text())
for row in manifest:
 assert hashlib.sha256((tree/'vendor/asus/p00a'/row['path']).read_bytes()).hexdigest()==row['sha256']
backup=root/'before-graphics-profile-r6'; backup.mkdir()
p=tree/'system/linkerconfig/contents/tests/configuration/p00a_legacy_graphics_test.cc'
shutil.copyfile(p,backup/p.name)
subprocess.run(['git','apply','--check',str(root/'revisions/r6/from-r5.patch')],cwd=tree/'system/linkerconfig',check=True)
subprocess.run(['git','apply',str(root/'revisions/r6/from-r5.patch')],cwd=tree/'system/linkerconfig',check=True)
expected=json.loads((root/'revisions/r6/source-manifest.json').read_text())
for name,row in expected.items():
 assert hashlib.sha256((tree/'system/linkerconfig'/name).read_bytes()).hexdigest()==row['after_sha256'],name
(root/'logs/graphics-deploy-r6.json').write_text(json.dumps(dict(revision='r6', inputs_revision='r5', verified_files=len(manifest), exit_status=0, change='test include order only'),indent=2)+'\\n')
print('r6 deployed and verified; r5 graphics inputs unchanged; exit 0')
'''
subprocess.run(SSH+['python3 -'],input=script.encode(),check=True)
