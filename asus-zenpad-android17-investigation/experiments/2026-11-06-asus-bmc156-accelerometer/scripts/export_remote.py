from pathlib import Path
import tarfile,hashlib,json,shutil
R=Path('/srv/android/asus-bmc156-accelerometer-r1');H=R/'handoff';H.mkdir(exist_ok=True)
verified=json.loads((R/'evidence/final-verification.json').read_text())
for rel,row in verified['source_changes'].items():
 assert hashlib.sha256((R/'source/kernel'/rel).read_bytes()).hexdigest()==row['after'],rel
assert hashlib.sha256((R/'hal-out/sensors.mt8163.so').read_bytes()).hexdigest()==verified['hal_sha256']
for p in (R/'evidence').iterdir():
 if p.is_file() and p.name!='baseline-source-hashes.json':
  d=H/'evidence'/p.name;d.parent.mkdir(exist_ok=True);shutil.copyfile(p,d)
for src,rel in [(R/'hal-out/sensors.mt8163.so','artifacts/sensors.mt8163.so')]+[(R/'out'/p,'artifacts/kernel-objects/'+Path(p).name) for p in ['drivers/misc/mediatek/sensors-1.0/accelerometer/bmc156_acc/bmc156_acc.o','drivers/misc/mediatek/sensors-1.0/accelerometer/accel.o','drivers/misc/mediatek/sensors-1.0/hwmon/sensor_attributes/sensor_attr.o','drivers/misc/mediatek/sensors-1.0/built-in.o']]:
 d=H/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,d)
for p in (R/'sdk/reference').rglob('*'):
 if p.is_file():
  d=H/'references'/p.relative_to(R/'sdk/reference');d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d)
manifest={str(p.relative_to(H)):hashlib.sha256(p.read_bytes()).hexdigest() for p in H.rglob('*') if p.is_file() and p.name!='export-manifest.json'}
(H/'export-manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
with tarfile.open(R/'handoff.tar.gz','w:gz') as t:
 for p in H.rglob('*'):
  if p.is_file():t.add(p,arcname=str(p.relative_to(H)))
p=R/'handoff.tar.gz';print(json.dumps(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()),indent=2))
