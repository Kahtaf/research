#!/usr/bin/env python3
"""Apply the two verified API/build-definition adaptations on the Linux VM."""
import json,re,subprocess
from pathlib import Path
root=Path('/srv/android/asus-android17');source=root/'kernel'
p=source/'fs/erofs/inode.c';s=p.read_text()
old='\tstat->attributes_mask |= (STATX_ATTR_COMPRESSED |\n\t\t\t\t  STATX_ATTR_IMMUTABLE);'
assert s.count(old)==1;s=s.replace(old,'\t/* This MT8163 VFS reports the common statx attribute mask globally. */');p.write_text(s)
subprocess.run(['git','add','fs/erofs/inode.c'],cwd=source,check=True)
subprocess.run(['git','commit','-m','erofs: match MT8163 kstat attribute representation',
 '-m','This baseline has kstat.attributes but no per-filesystem attributes_mask. fs/stat.c supplies STATX_ATTR_ALL. Keep the supported immutable/compressed flags.'],cwd=source,check=True)
(root/'patches/0010-mt8163-erofs-kstat.patch').write_bytes(subprocess.check_output(['git','format-patch','-1','--stdout'],cwd=source))

project=Path('/srv/android/lineage24/prebuilts/misc')
p=project/'protobuf_vendorcompat/Android.bp';s=p.read_text()
names=re.findall(r'name:\s*"(libprotobuf[^\"]+)"',s)
assert sorted(names)==['libprotobuf-cpp-full-21.12-vendorcompat','libprotobuf-cpp-lite-21.12-vendorcompat']
assert s.count('cc_prebuilt_library_shared {')==2
prefix=s.split('cc_prebuilt_library_shared {',1)[0]
p.write_text(prefix+'// The arm/arm64 definitions are supplied by hardware/lineage/compat.\n')
patch=root/'patches/platform-0001-protobuf-dedup.patch'
patch.write_bytes(subprocess.check_output(['git','diff','--','protobuf_vendorcompat/Android.bp'],cwd=project))
(root/'logs/platform-patch-manifest.json').write_text(json.dumps({
 'project':'prebuilts/misc','base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=project,text=True).strip(),
 'patch':str(patch.relative_to(root)),
 'reason':'Remove obsolete arm-only duplicate definitions; retain existing arm/arm64 hardware/lineage/compat definitions.'},indent=2)+'\n')
