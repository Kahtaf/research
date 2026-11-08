#!/usr/bin/env python3
"""Inspect pulled vendor ELF files in the audit container; never execute them."""
import json,re,subprocess
from pathlib import Path
root=Path('/audit'); device=root/'evidence/device'; rows=[]
paths=sorted({p for folder in ['vendor','system-lib-hw','system-lib64-hw'] for p in (device/folder).rglob('*') if p.is_file() and p.read_bytes()[:4]==b'\x7fELF'})
for p in paths:
 if not any(x in p.name for x in ['libGLES_mali','hwcomposer','gralloc.','audio.primary','camera.mt','sensors.mt']):continue
 hdr=subprocess.check_output(['readelf','-h',str(p)],text=True)
 dynamic=subprocess.check_output(['readelf','-d',str(p)],text=True)
 symbols=subprocess.check_output(['readelf','--dyn-syms','--wide',str(p)],text=True)
 rows.append(dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,elf_class=re.search(r'Class:\s+(\S+)',hdr).group(1),needed=re.findall(r'Shared library: \[(.*?)\]',dynamic),undefined_symbols=[l.split()[-1] for l in symbols.splitlines() if ' UND ' in l]))
(root/'evidence/vendor-abi.json').write_text(json.dumps(dict(elf_files_total=len(paths),samples=rows),indent=2)+'\n')
print('ELF files:',len(paths),'key samples:',len(rows))
for row in rows:print(row['path'],row['elf_class'],'dependencies:',len(row['needed']),'undefined:',len(row['undefined_symbols']))
