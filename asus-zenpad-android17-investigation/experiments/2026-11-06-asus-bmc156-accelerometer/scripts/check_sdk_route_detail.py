from pathlib import Path
import hashlib,json,shutil
A=Path('/srv/android/lineage24');R=Path('/srv/android/asus-bmc156-accelerometer-r1')
for rel in ['frameworks/native/services/sensorservice/HidlSensorHalWrapper.cpp','frameworks/native/services/sensorservice/SensorDevice.cpp']:
 p=A/rel;s=p.read_text();print('FILE',rel,'SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
 if 'HidlSensor' in rel: print('\n'.join(s.splitlines()[395:455]))
 else:
  lines=s.splitlines()
  for i,l in enumerate(lines):
   if any(w in l for w in ['HidlSensorHalWrapper','AidlSensorHalWrapper','connectHidlService']):print('\n'.join(f'{j+1}: {lines[j]}' for j in range(max(0,i-7),min(len(lines),i+10))))
 dst=R/'sdk/reference'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
