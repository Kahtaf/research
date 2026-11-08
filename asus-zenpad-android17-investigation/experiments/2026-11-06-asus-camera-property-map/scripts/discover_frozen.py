from pathlib import Path
import json,subprocess
r=Path('/srv/android/asus-camera-property-map-20261106');r.mkdir(exist_ok=False)
for name in ['asus-camera-arm32-route','asus-camera-source-abi-route']:
 b=Path('/srv/android')/name
 print('FROZEN',b)
 print('TOP', sorted(p.name for p in b.iterdir()))
 for rel in ['sdk37/system/core/libutils/include/utils','cpp-out/sdk37/system/core/libutils/include/utils','sdk37-libs','abi-out','public']:
  p=b/rel
  if p.is_dir(): print(rel,sorted(x.name for x in p.iterdir()))
print('HOST_TOOLS',subprocess.run(['sh','-c','command -v clang++; command -v g++; command -v qemu-arm; command -v qemu-aarch64'],capture_output=True,text=True).stdout)
