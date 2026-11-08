from pathlib import Path
b=Path('/srv/android/lineage24')
for base in ['out/soong/.intermediates/hardware/interfaces/graphics/common/aidl','frameworks/native/libs/input','frameworks/native/include/input']:
 p=b/base;print(base)
 if p.exists():
  if 'out/' in base:
   for q in p.glob('*/gen/include'):print(q.relative_to(b))
  else:print([q.name for q in p.iterdir()][:60])
