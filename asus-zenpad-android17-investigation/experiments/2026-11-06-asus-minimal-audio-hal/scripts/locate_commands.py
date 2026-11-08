from pathlib import Path
import subprocess,os,resource
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
a=Path('/srv/android/lineage24')
for p in [a/'out/soong/build.lineage_p00a.0.ninja',a/'out/soong/build.lineage_p00a.1.ninja']:
 print(p,p.stat().st_size)
 with p.open() as f:print(f.read(1000))
for p in (a/'out/soong').glob('build.lineage_p00a*.ninja'):
 r=subprocess.run(['rg','-n','-m','3','audio.primary.default|external/tinyalsa/pcm.c',str(p)],capture_output=True,text=True)
 if r.stdout:print(r.stdout[:20000])
