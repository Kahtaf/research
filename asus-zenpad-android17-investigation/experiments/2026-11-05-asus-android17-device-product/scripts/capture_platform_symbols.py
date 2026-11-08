#!/usr/bin/env python3
"""Record exports from actual compiled Android 17 libraries, without running them."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path('/srv/android/asus-device-product')
PRODUCT = Path('/srv/android/lineage24/out/target/product/p00a')
NAMES = set('libc.so libdl.so libm.so liblog.so libutils.so libcutils.so libhardware.so libhardware_legacy.so libsync.so libui.so libgui.so libbinder.so libnativewindow.so libandroid.so libandroid_runtime.so libEGL.so libGLESv1_CM.so libGLESv2.so libGLESv3.so libcrypto.so libssl.so libz.so libbase.so libstdc++.so libc++.so'.split())
rows = []
for directory in ('lib', 'lib64'):
    for name in sorted(NAMES):
        candidates = [PRODUCT / 'system' / directory / name,
                      PRODUCT / 'system' / directory / 'bootstrap' / name]
        path = next((path for path in candidates if path.is_file()), None)
        if not path:
            continue
        data = path.read_bytes()
        if data[:4] != b'\x7fELF':
            continue
        text = subprocess.check_output(['readelf', '--dyn-syms', '--wide', str(path)], text=True)
        exports = set()
        for line in text.splitlines():
            match = re.match(r'^\s*\d+:\s+[0-9a-fA-F]+\s+\d+\s+.+?\s+(GLOBAL|WEAK)\s+\S+\s+(\S+)\s+(\S+)', line)
            if match and match[2] != 'UND':
                exports.add(match[3].split('@')[0])
        rows.append(dict(name=name, path=str(path), bits=32 if data[4] == 1 else 64,
                         sha256=hashlib.sha256(data).hexdigest(), exports=sorted(exports)))
output = ROOT / 'compatibility/platform-library-exports.json'
output.write_text(json.dumps(dict(scope='Compiled ELF exports only; source build may still be in progress', libraries=rows), indent=2) + '\n')
print(f'Captured {len(rows)} compiled core libraries into {output}')
