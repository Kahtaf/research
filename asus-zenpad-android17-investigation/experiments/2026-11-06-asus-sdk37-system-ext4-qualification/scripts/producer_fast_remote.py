import os,resource,pathlib,json,hashlib,subprocess,datetime
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
P=pathlib.Path;A=P('/srv/android/lineage24');R=P('/srv/android/asus-sdk37-system-ext4-qualification-20261106');d={'prior_python_scan':'No receipt; bounded process terminated with empty SSH-wrapper RuntimeError. No producer command executed.','matches':{}}
needle='out/soong/.intermediates/system/extras/ext4_utils/mkuserimg_mke2fs/linux_glibc_x86_64/mkuserimg_mke2fs'
for p in sorted((A/'out/soong').glob('build*.ninja')):
 r=subprocess.run(['/usr/bin/grep','-n','-F','-B','3','-A','14','--',needle,str(p)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30)
 if r.stdout:
  assert len(r.stdout)<1000000;d['matches'][str(p)]={'exit':r.returncode,'text':r.stdout,'sha256':hashlib.sha256(r.stdout.encode()).hexdigest()}
d['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(R/'wrapper-producer.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
