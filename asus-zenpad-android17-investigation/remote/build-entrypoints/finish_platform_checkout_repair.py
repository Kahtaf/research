#!/usr/bin/env python3
"""Verify source pins/index recovery and replay only the recorded platform edits."""
import json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
platform=Path('/srv/android/lineage24');root=Path('/srv/android/asus-android17')
assert Path('/srv/android/logs/platform-checkout-repaired').exists()
def pins(path):
    return {p.attrib.get('path',p.attrib['name']):p.attrib['revision'] for p in ET.parse(path).getroot().findall('project')}
before=pins('/srv/android/logs/resolved-manifest.xml')
after=pins('/srv/android/logs/resolved-manifest-after-repair.xml')
assert before==after and len(after)==1239
project=platform/'device/google/cuttlefish_vmm'
tracked=subprocess.check_output(['git','ls-files'],cwd=project).splitlines()
assert len(tracked)>100
status=subprocess.check_output(['git','status','--porcelain'],cwd=project)
(root/'logs/cuttlefish-after-repair-status.txt').write_bytes(status)
assert not status.strip(), 'Unexpected leftover files in repaired prebuilt project'
rows=[json.loads((root/'logs/platform-patch-manifest.json').read_text()),
      *json.loads((root/'logs/platform-jxl-patches.json').read_text())]
for row in rows:
    cwd=platform/row['project'];patch=root/row['patch']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=cwd,text=True).strip()==row['base_commit']
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=cwd).strip()
    subprocess.run(['git','apply','--check',str(patch)],cwd=cwd,check=True)
    subprocess.run(['git','apply',str(patch)],cwd=cwd,check=True)
(root/'logs/platform-repair-verification.json').write_text(json.dumps(dict(
    project_pins_unchanged=1239,cuttlefish_tracked_files=len(tracked),cuttlefish_clean=True,
    platform_patches_replayed=len(rows)),indent=2)+'\n')
print('Platform pins unchanged; prebuilt index restored; four reviewed patches replayed.')
