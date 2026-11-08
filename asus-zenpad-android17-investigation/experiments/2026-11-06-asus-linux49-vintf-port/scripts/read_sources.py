from pathlib import Path
import json, hashlib, base64, subprocess
s=Path('/srv/android/lineage24')
files=['system/libvintf/'+f for f in ['VintfObject.cpp','RuntimeInfo.cpp','KernelInfo.cpp','CompatibilityMatrix.cpp','HalManifest.cpp','assemble_vintf.cpp','check_vintf.cpp','parse_xml.cpp']]
files += ['hardware/interfaces/compatibility_matrices/Android.bp','hardware/interfaces/compatibility_matrices/build/vintf_compatibility_matrix.go','kernel/configs/Android.bp','kernel/configs/build/kernel_config.go','build/make/core/Makefile','build/make/core/board_config.mk','device/asus/p00a/BoardConfig.mk','device/asus/p00a/manifest.xml']
r={}
for f in files:
 p=s/f
 if p.is_file():
  b=p.read_bytes();r[f]={'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode()}
print(json.dumps(r))
