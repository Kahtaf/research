#!/usr/bin/env python3
"""Read actual builder ELF exports; does not alter the source tree."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

T = Path('/srv/android/lineage24')
I = T / 'out/soong/.intermediates'
log = Path('/srv/android/asus-device-product/logs/graphics-collect-r4.log').read_text()
symbols = sorted(set(re.findall(r'error: Unresolved symbol: (\S+)', log)))
providers = {'libc': 'bionic/libc/libc', 'libbinder': 'frameworks/native/libs/binder/libbinder',
             'libsync': 'system/core/libsync/libsync', 'liblog': 'system/logging/liblog/liblog'}
rows=[]
for bits,arch in [(32,'arm_armv8-a_cortex-a53'),(64,'arm64_armv8-a')]:
    for name,project in providers.items():
        for variant in ['core','vendor']:
            path = I / project / f'android_{"vendor_" if variant == "vendor" else ""}{arch}_shared' / (name+'.so')
            if not path.exists(): continue
            output = subprocess.check_output(['readelf','--dyn-syms','--wide',str(path)], text=True)
            exports=set()
            for line in output.splitlines():
                parts=line.split()
                if len(parts)>7 and parts[0].endswith(':') and parts[6]!='UND':
                    exports.add(parts[7].split('@')[0])
            rows.append(dict(bits=bits, library=name, variant=variant, path=str(path),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                resolves_r4_symbols=[s for s in symbols if s.split('@')[0] in exports]))
print(json.dumps(dict(r4_unresolved_symbols=symbols, providers=rows),indent=2))
