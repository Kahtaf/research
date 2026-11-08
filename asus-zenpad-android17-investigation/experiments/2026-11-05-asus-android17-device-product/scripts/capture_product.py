#!/usr/bin/env python3
"""Run on the Linux builder after both named build services are terminal."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tarfile

root = Path('/srv/android/lineage24')
run = Path('/srv/android/asus-device-product')
out = run / 'result'
out.mkdir(exist_ok=True)
assert (run / 'logs/init-adbd-build-complete').exists()
for source, name in [
    ('out/target/product/p00a/system/bin/init', 'android17-p00a-init'),
    ('out/target/product/p00a/apex/com.android.adbd/bin/adbd', 'android17-p00a-adbd'),
    ('out/target/product/p00a/system/apex/com.android.adbd.capex', 'com.android.adbd.capex'),
]:
    shutil.copy2(root / source, out / name)
for name in ('android17-p00a-init', 'android17-p00a-adbd'):
    text = subprocess.check_output(['readelf', '-h', '-l', str(out / name)], text=True)
    assert 'ELF64' in text and 'AArch64' in text
    interpreter = ('/system/bin/bootstrap/linker64' if name.endswith('-init')
                   else '/system/bin/linker64')
    assert f'Requesting program interpreter: {interpreter}]' in text
    (out / (name + '-elf.txt')).write_text(text)

logs = out / 'logs'
logs.mkdir(exist_ok=True)
for path in (run / 'logs').glob('*'):
    if path.is_file():
        shutil.copy2(path, logs / path.name)
for name in ('asus-device-product-armv8.log', 'asus-device-product-clean.log',
             'asus-device-product-apex.log', 'asus-device-product-headers.log',
             'asus-device-product-headers-target.log'):
    shutil.copy2(Path('/srv/android/logs') / name, logs / name)
for name in ('build_product.sh', 'build_headers.sh'):
    shutil.copy2(Path('/srv/android') / name, logs / ('executed-' + name))

patches = out / 'patches'
patches.mkdir(exist_ok=True)
for repo in ('external/skia', 'external/google-highway', 'external/XMP-Toolkit-SDK'):
    diff = subprocess.check_output(['git', '-C', str(root / repo), 'diff', '--', 'Android.bp'])
    assert diff
    (patches / (repo.replace('/', '_') + '.patch')).write_bytes(diff)
assert not subprocess.check_output(['git', '-C', str(root / 'prebuilts/misc'), 'diff'])

with tarfile.open(out / 'device-config.tar.gz', 'w:gz') as archive:
    archive.add(root / 'device/asus/p00a', arcname='device/asus/p00a')

headers_complete = (run / 'logs/kernel-header-build-complete').exists()
if headers_complete:
    folder = root / 'out/soong/.intermediates/vendor/lineage/build/soong/generated_kernel_includes/gen'
    assert (folder / 'usr/include/linux/version.h').is_file(), folder
    with tarfile.open(out / 'generated-kernel-headers.tar.gz', 'w:gz') as archive:
        archive.add(folder / 'usr', arcname='usr')

rows = []
for path in sorted(out.rglob('*')):
    if path.is_file() and path.name != 'manifest.json':
        data = path.read_bytes()
        rows.append(dict(path=str(path.relative_to(out)), bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
manifest = dict(stage='Android 17 init + device ADB APEX module build only', sdk=37,
                kernel_header_build_passed=headers_complete, flashable_rom=False, files=rows)
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
with tarfile.open(run / 'checkpoint.tar.gz', 'w:gz') as archive:
    archive.add(out, arcname='result')
print(json.dumps(dict(files=len(rows), kernel_headers=headers_complete, archive=str(run / 'checkpoint.tar.gz'))))
