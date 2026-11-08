from pathlib import Path
import json,hashlib,base64,subprocess
S=Path('/srv/android/lineage24');r={}
for sub in ['system/libvintf','system/libhidl/vintfdata','system/libhidl/transport','build/soong/vintf','system/core/init']:
 root=S/sub
 if not root.exists():continue
 for p in root.rglob('*'):
  if p.is_file() and p.suffix in ['.cpp','.h','.go','.py','.bp','.mk'] and p.stat().st_size<500000:
   b=p.read_bytes()
   if any(t in b for t in [b'first_api_level',b'PRODUCT_SHIPPING_API_LEVEL',b'VINTF_IGNORE_TARGET_FCM_VERSION',b'kEnforceDeviceManifestNoKernelLevel']):
    r[str(p.relative_to(S))]={'base64':base64.b64encode(b).decode(),'sha256':hashlib.sha256(b).hexdigest()}
print(json.dumps(r))
