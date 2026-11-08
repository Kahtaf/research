from pathlib import Path
import json,hashlib,base64,subprocess
s=Path('/srv/android/lineage24');files=['system/libvintf/AssembleVintf.cpp','system/libvintf/assemble_vintf_main.cpp','system/libvintf/include/vintf/Level.h','system/libvintf/MatrixKernel.cpp','system/libvintf/RuntimeInfo.cpp','hardware/interfaces/compatibility_matrices/build/vintf_compatibility_matrix.go','kernel/configs/build/kernel_config.go','kernel/configs/tools/Android.bp','kernel/configs/t/android-4.14/Android.bp']
r={}
for f in files:
 p=s/f
 if p.is_file():
  b=p.read_bytes();r[f]={'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode()}
r['history']={}
for d,args in [('kernel/configs',['log','-8','--format=%H %s','--all','--','q/android-4.9','p/android-4.9','android-4.9']),('system/libvintf',['ls-files','*Assemble*'])]:
 r['history'][d]=subprocess.run(['git','-C',str(s/d)]+args,capture_output=True,text=True,timeout=20).stdout
print(json.dumps(r))
