from pathlib import Path
import subprocess,json,hashlib,shutil,os
R=Path('/srv/android/asus-bmc156-accelerometer-r1');A=Path('/srv/android/lineage24');B=Path('/srv/android/asus-build-continuation/policy-vendor-r4');O=R/'policy';O.mkdir(exist_ok=True)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
e=json.loads((B/'evidence.json').read_text());cmd=e['m4_command']
# Independently copy the previously reviewed generator inputs and redirects.
new=[];pins={}
for a in cmd:
 p=Path(a)
 if p.is_file() and str(p).startswith(str(B)):
  d=O/p.relative_to(B);d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d);new.append(str(d));pins[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 else:new.append(a)
idx=next(i for i,a in enumerate(new) if a.endswith('/roles_decl'))
new[idx:idx]=[str(R/'source/hal/sepolicy/p00a_accelerometer.te'),str(O/'newline')]
new += [str(R/'source/hal/sepolicy/genfs_contexts'),str(O/'newline')]
conf=O/'policy.conf'
with conf.open('wb') as f:p=subprocess.run(new,stdout=f,stderr=subprocess.PIPE)
assert p.returncode==0,p.stderr
cmd=[str(A/'out/host/linux-x86/bin/checkpolicy'),'-C','-M','-c','30','-o',str(O/'policy.cil'),str(conf)]
p=subprocess.run(cmd,capture_output=True,text=True)
res=dict(m4_command=new,command=cmd,exit=p.returncode,stdout=p.stdout,stderr=p.stderr,inputs=pins)
(R/'evidence/policy-compile.json').write_text(json.dumps(res,indent=2)+'\n');print(p.returncode,p.stdout,p.stderr);assert p.returncode==0

for p in (O/'source/system/sepolicy').rglob('*.te'):
 for line in p.read_text().splitlines():
  if 'sensors_vendor_data_file' in line or 'vendor_sensors_data_file' in line:print(p.name,line)
