from pathlib import Path
import os,resource,hashlib,subprocess,json
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
b=Path('/srv/android/lineage24');p=b/'out/soong/.intermediates/hardware/interfaces/camera/provider/2.4/default';rows=[]
if p.exists():
 for f in p.glob('*/*/*'):
  if f.is_file() and (f.name.endswith('.so') or f.name.startswith('android.hardware.camera.provider@2.4-service')) and f.stat().st_size<10*1024**2:
   data=f.read_bytes()
   if data.startswith(b'\x7fELF'):
    rows.append({'path':str(f),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
print(json.dumps({'scoped_directory':str(p),'exists':p.exists(),'built_elfs':rows,'limit':'Exact current provider module directory and immediate variant outputs only; not a full out scan.'},indent=2))
