from pathlib import Path
import hashlib,json
A=Path('/srv/android/lineage24');R=Path('/srv/android/asus-bmc156-accelerometer-r1');rows={}
for rel in ['hardware/libhardware/Android.bp','frameworks/native/data/etc/android.hardware.sensor.accelerometer.xml']:
 p=A/rel;assert p.is_file();print('FILE',rel,'SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
 if rel.endswith('.bp'):
  text=p.read_text();i=text.index('name: "libhardware_headers"');print(text[i:i+1000])
 else:print(p.read_text())
 rows[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in (A/'frameworks/native/services/sensorservice').rglob('*'):
 if p.is_file() and p.suffix in ['.cpp','.h']:
  lines=p.read_text().splitlines();matched=[f'{i}: {l}' for i,l in enumerate(lines,1) if any(x in l for x in ['V1_0::ISensors','V1_0','connectHidl','ISensors::getService','HalConnectionStatus','HalWrapperV1','HalWrapperHidl'])]
  if matched:
   rel=str(p.relative_to(A));print('FILE',rel,'SHA256',hashlib.sha256(p.read_bytes()).hexdigest());print('\n'.join(matched));rows[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
(R/'evidence/sdk-route-pins.json').write_text(json.dumps(rows,indent=2)+'\n')
