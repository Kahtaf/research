from pathlib import Path
import os,resource,json,hashlib,base64
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
a=Path('/srv/android/lineage24')
for p in a.glob('external/tinyalsa*'):print('DIR',p)
for p in a.glob('external/tinyalsa*/**/asoundlib.h'):print('HEADER',p,'pcm_writei' in p.read_text())
for p in a.glob('out/soong/.intermediates/external/tinyalsa*/**/libtinyalsa*.so'):
 if 'arm64' in str(p):print('ELF',p,p.stat().st_size)
# Global variable lines referenced by captured compile edge.
f=a/'out/soong/build.lineage_p00a.ninja'
for l in f.open():
 if l.startswith(('g.android.soong.cc.config.','ccCmd =','g.cc.')):print(l.rstrip())
