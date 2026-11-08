import os,resource,pathlib,json,hashlib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(120,120))
P=pathlib.Path;A=P('/srv/android/lineage24');R=P('/srv/android/asus-sdk37-system-ext4-qualification-20261106');needle='out/soong/.intermediates/system/extras/ext4_utils/mkuserimg_mke2fs/linux_glibc_x86_64/mkuserimg_mke2fs';d={}
for p in (A/'out/soong').glob('build*.ninja'):
 hits=[];pending='';physical=[];active=False
 with p.open() as f:
  for line in f:
   physical.append(line.rstrip());pending+=line.rstrip().removesuffix('$')
   if line.rstrip().endswith('$'):continue
   if pending.startswith('build '):active=needle in pending.split(':',1)[0]
   if active:hits+=physical
   pending='';physical=[]
 if hits:d[str(p)]={'physical_lines':hits,'sha256':hashlib.sha256(('\n'.join(hits)+'\n').encode()).hexdigest()}
(R/'wrapper-producer.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
