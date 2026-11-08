from pathlib import Path
b=Path('/srv/android/lineage24')
for rel in ['system/libfmq','system/libbase','system/libhidl']:
 p=b/rel;print(rel,p.exists());print([str(x.relative_to(b)) for x in p.rglob('MQDescriptorBase.h')]);print([x.name for x in p.iterdir()][:30] if p.exists() else [])
