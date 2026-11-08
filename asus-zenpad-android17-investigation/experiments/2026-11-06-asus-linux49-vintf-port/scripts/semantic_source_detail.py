from pathlib import Path
import subprocess,json,hashlib,base64
S=Path('/srv/android/lineage24');r={}
for sub,pattern in [('build/soong','*vintf*'),('system/libvintf','*RuntimeInfo*')]:
 r[sub]=subprocess.run(['find',str(S/sub),'-maxdepth','3','-iname',pattern],capture_output=True,text=True,timeout=10).stdout
for f in ['system/libvintf/RuntimeInfo-target.cpp','system/libvintf/RuntimeInfo-host.cpp','system/libvintf/include/vintf/CheckFlags.h','system/libhidl/vintfdata/Android.bp']:
 p=S/f
 if p.is_file():
  b=p.read_bytes();r[f]={'base64':base64.b64encode(b).decode(),'sha256':hashlib.sha256(b).hexdigest()}
print(json.dumps(r))
