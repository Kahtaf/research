#!/usr/bin/env python3
"""Run on the existing Linux builder; attach the pinned kernel and ASUS product."""
from pathlib import Path
import json,subprocess,tarfile
platform=Path('/srv/android/lineage24');root=Path('/srv/android/asus-device-product')
root.mkdir(exist_ok=True);(root/'logs').mkdir(exist_ok=True)
original=Path('/srv/android/asus-android17/kernel')
pin=json.loads(Path('/srv/android/asus-android17/result/manifest.json').read_text())['feature_commit']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=original,text=True).strip()==pin
assert not subprocess.check_output(['git','status','--porcelain'],cwd=original).strip()
target=platform/'kernel/asus/p00a';target.parent.mkdir(parents=True,exist_ok=True)
if not target.exists():
    subprocess.run(['git','worktree','add','--detach',str(target),pin],cwd=original,check=True)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=target,text=True).strip()==pin
assert not (platform/'device/asus/p00a').exists(), 'Do not overwrite an existing device product'
with tarfile.open('/srv/android/device-product-inputs.tar.gz') as t:
    t.extractall(platform,filter='data')
(root/'logs/source-pin.json').write_text(json.dumps(dict(kernel_commit=pin,
    kernel_path='kernel/asus/p00a',hardware='ASUS P00A_2 / MT8163',stage='init/adbd modules; images disabled'),indent=2)+'\n')
print('ASUS product deployed with an independent worktree of the verified kernel source.')
