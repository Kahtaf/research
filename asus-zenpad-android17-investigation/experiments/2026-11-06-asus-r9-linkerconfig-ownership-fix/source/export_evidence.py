from pathlib import Path
import os,json,base64,hashlib
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');files=[]
for p in (R/'evidence').iterdir():
 if p.is_file() and p.suffix in ['.json','.log','.txt']:files.append(p)
for d in ['run-patch-r1','run-runtime-r1','run-patch-r2','run-runtime-r2','run-patch-r3','run-runtime-r3']:
 p=R/d
 if p.is_dir():files += [f for f in p.iterdir() if f.is_file() and f.suffix in ['.json','.log']]
# Small generated configurations and executed source copies, never disks/entropy-bearing CPIO.
files += [p for p in (R/'work').glob('actual-*.ld.config.txt') if p.is_file()]
for n in ['runtime_observer.c','runtime_patcher_r2.c','prepare_runtime_r2_actual.py','prepare_runtime_r2_resumed.py','execute_runtime_r2.py']:
 p=R/'source'/n
 if p.is_file():files.append(p)
D={}
for p in files:
 assert p.stat().st_size<8*1024**2,p;b=p.read_bytes();D[str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode()}
print(json.dumps(D))
