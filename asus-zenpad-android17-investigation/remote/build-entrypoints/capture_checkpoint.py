#!/usr/bin/env python3
"""Capture the compiled EROFS candidate, source patches and exact source pins."""
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
root=Path('/srv/android/asus-android17');source=root/'kernel';result=root/'result'
assert (root/'logs/erofs-build-complete').exists()
assert not subprocess.check_output(['git','status','--porcelain'],cwd=source).strip()
base=(root/'logs/baseline-commit.txt').read_text().strip()
patch=root/'patches/combined-erofs-on-asus-hardware.patch'
patch.write_bytes(subprocess.check_output(['git','diff',base,'HEAD','--'],cwd=source))
check=subprocess.run(['git','apply','--check',str(patch)],
    cwd='/srv/android/asus-hardware/sources/kernel',capture_output=True,text=True)
(root/'logs/combined-patch-check.txt').write_text(check.stdout+check.stderr+f'exit={check.returncode}\n')
check.check_returncode()
result.mkdir(exist_ok=True)
for folder in ['patches','logs']:
    shutil.copytree(root/folder,result/folder,dirs_exist_ok=True)
for src,name in [
    ('arch/arm64/boot/Image.gz-dtb','ASUS-P00A-EROFS-UNTESTED.Image.gz-dtb'),
    ('arch/arm64/boot/dts/mediatek/asus-p00a.dtb','asus-p00a.dtb'),
    ('.config','kernel.config')]:
    shutil.copyfile(root/'build-erofs'/src,result/name)
(result/'source-history.txt').write_bytes(subprocess.check_output(
    ['git','log','--format=%H%x09%s',base+'..HEAD'],cwd=source))
files=[]
for p in sorted(result.rglob('*')):
    if p.is_file() and p != result/'manifest.json':
        files.append(dict(path=str(p.relative_to(result)),bytes=p.stat().st_size,
            sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(result/'manifest.json').write_text(json.dumps(dict(
    hardware_baseline_commit=base,feature_commit=subprocess.check_output(
        ['git','rev-parse','HEAD'],cwd=source,text=True).strip(),
    combined_patch_applies_to_hardware=True,compiled=True,runtime_tested=False,
    is_android17_rom=False,flash_ready=False,files=files),indent=2)+'\n')
with tarfile.open(root/'checkpoint.tar.gz','w:gz') as t:
    t.add(result,arcname='.')
print('Captured EROFS build and replay-checkable source; no runtime or flashing claim.')
