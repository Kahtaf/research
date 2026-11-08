#!/usr/bin/env python3
"""Supply actual vendor build variants required by Lineage's libjxl declaration."""
import json,re,subprocess
from pathlib import Path
platform=Path('/srv/android/lineage24');root=Path('/srv/android/asus-android17')
rows=[]
for project,modules in [('external/skia',['libskia_skcms']),('external/google-highway',['libhwy']),('external/XMP-Toolkit-SDK',['xmp_toolkit_sdk','zuid_md5'])]:
    p=platform/project/'Android.bp';s=p.read_text()
    for module in modules:
        anchor=f'    name: "{module}",\n'
        assert s.count(anchor)==1
        start=s.index(anchor);end=s.find('\n}',start)
        if 'vendor_available:' not in s[start:end]:
            s=s.replace(anchor,anchor+'    vendor_available: true,\n',1)
        else:
            assert 'vendor_available: true,' in s[start:end]
    p.write_text(s)
    patch=root/'patches'/('platform-0002-'+modules[0]+'-vendor.patch')
    patch.write_bytes(subprocess.check_output(['git','diff','--','Android.bp'],cwd=platform/project))
    rows.append(dict(project=project,modules=modules,base_commit=subprocess.check_output(
        ['git','rev-parse','HEAD'],cwd=platform/project,text=True).strip(),patch=str(patch.relative_to(root))))
(root/'logs/platform-jxl-patches.json').write_text(json.dumps(rows,indent=2)+'\n')
