import shutil,json
from pathlib import Path
r=Path('/srv/android/asus-camera-property-map-20261106')
print('TOOLS',{x:shutil.which(x) for x in ['patchelf','objcopy','valgrind','qemu-arm','qemu-aarch64']})
d=json.loads((r/'commands.json').read_text());print('LAST',d[-1]['rc'],d[-1]['stderr'][:3000])
for arch in ['arm','arm64']:
 p=r/arch/'layouts.txt'
 if p.exists():
  s=p.read_text();print(arch,'\n'.join(b for b in s.split('*** Dumping AST Record Layout') if any(x in b for x in ['class android::AsusPropMap\n','class android::VectorImpl\n','class android::String8\n','Vtable for'])))
