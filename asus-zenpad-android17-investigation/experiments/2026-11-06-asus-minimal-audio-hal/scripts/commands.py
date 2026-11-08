from pathlib import Path
import os,re
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
a=Path('/srv/android/lineage24')
f=a/'out/soong/build.lineage_p00a.ninja'
for l in f.open():
 if l.startswith(('subninja','include')):print(l.rstrip())
# Soong shards hold compile edges, capture complete relevant blocks and rules.
for f in (a/'out/soong').glob('build.lineage_p00a.[0-9].ninja'):
 block=[]
 for line in f.open():
  if line.startswith(('build ','rule ')):
   if block and ('audio.primary.default/android_vendor_arm64' in block[0] or ('libtinyalsa/android_arm64' in block[0])):print('FILE',f,'\n'+''.join(block))
   block=[line]
  else:block.append(line)
