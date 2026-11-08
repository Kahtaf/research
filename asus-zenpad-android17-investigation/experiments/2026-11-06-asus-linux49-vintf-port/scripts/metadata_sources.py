from pathlib import Path
import json,base64,hashlib
S=Path('/srv/android/lineage24');P=Path('/srv/android/asus-linux49-vintf-port-20261106')
files=list((S/'system/libvintf').glob('*.cpp'))+list((S/'system/libvintf/include').glob('**/*.h'))
r={}
for p in files:
 b=p.read_bytes()
 if b'first_api_level' in b or b'PRODUCT_SHIPPING_API_LEVEL' in b or b'VINTF_IGNORE_TARGET_FCM_VERSION' in b or b'ro.product.first_api_level' in b:
  r[str(p.relative_to(S))]={'base64':base64.b64encode(b).decode(),'sha256':hashlib.sha256(b).hexdigest()}
for f in ['system/etc/vintf/compatibility_matrix.7.xml','system/etc/vintf/compatibility_matrix.device.xml','vendor/etc/vintf/manifest.xml','vendor/etc/vintf/compatibility_matrix.xml','product/etc/vintf/compatibility_matrix.lineage.xml']:
 p=P/'baseline'/f;b=p.read_bytes();r['metadata/'+f]={'base64':base64.b64encode(b).decode(),'sha256':hashlib.sha256(b).hexdigest()}
for f in ['kernel/configs/t/android-4.14/android-base.config','kernel/configs/t/android-4.14/android-base-conditional.xml']:
 p=S/f;b=p.read_bytes();r[f]={'base64':base64.b64encode(b).decode(),'sha256':hashlib.sha256(b).hexdigest()}
print(json.dumps(r))
