from pathlib import Path
import json,base64,hashlib,os,resource
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
a=Path('/srv/android/lineage24');result={}
for pat in ['external/tinyalsa_new/include/tinyalsa/*.h','external/tinyalsa_new/src/*.[ch]','external/tinyalsa_new/Android.bp']:
 for p in a.glob(pat):result[str(p)]={'data':base64.b64encode(p.read_bytes()).decode(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
print(json.dumps(result))
