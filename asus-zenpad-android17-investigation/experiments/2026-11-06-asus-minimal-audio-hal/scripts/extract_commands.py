from pathlib import Path
import os,resource,subprocess
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
a=Path('/srv/android/lineage24')
paths=list((a/'out/soong').glob('build.lineage_p00a.[0-9].ninja'))
r=subprocess.run(['grep','-l','-m','1','# Module:  audio.primary.default',*map(str,paths)],capture_output=True,text=True)
for path in r.stdout.splitlines():
 p=Path(path);on=False;lines=[]
 for line in p.open():
  if line.startswith('# Module:'):
   on = line.strip()=='# Module:  audio.primary.default'
  if on: lines.append(line)
 print('FILE',path);print(''.join(lines))
# The global compiler/link rules are small relative to shards.
f=a/'out/soong/build.lineage_p00a.ninja';block=[]
for line in f.open():
 if line.startswith('rule '):
  if block and any(s in block[0] for s in ['cc.cc','cc.ld','cc.crt']):print(''.join(block))
  block=[line]
 else:block.append(line)
