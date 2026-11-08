from pathlib import Path
import json,base64,hashlib
S=Path('/srv/android/lineage24');r={}
for f in ['build/soong/android/vintf_data.go','build/soong/android/vintf_fragment.go','system/libhidl/vintfdata/Android.bp','system/libvintf/include/vintf/CheckFlags.h']:
 p=S/f;b=p.read_bytes();r[f]={'base64':base64.b64encode(b).decode(),'sha256':hashlib.sha256(b).hexdigest()}
print(json.dumps(r))
