from pathlib import Path
A=Path('/srv/android/lineage24/out/soong');p=A/'build.lineage_p00a.ninja'
with p.open() as f:
 for i,l in enumerate(f):
  if i<35 or l.startswith(('subninja','include ')):print(l.rstrip())
print('ninja matches')
for p in A.glob('*.ninja*'):print(p.name,p.stat().st_size)
