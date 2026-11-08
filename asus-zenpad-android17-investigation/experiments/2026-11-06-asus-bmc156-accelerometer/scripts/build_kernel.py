from pathlib import Path
import subprocess,json,hashlib,os,shutil,time
R=Path('/srv/android/asus-bmc156-accelerometer-r1');K=R/'kernel';O=R/'out'
os.environ['TMPDIR']=str(R/'tmp');(R/'tmp').mkdir(exist_ok=True)
# Single CPU and j1 only, with separately owned out and source.
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
for f in (R/'source/kernel').rglob('*'):
 if f.is_file():
  dest=K/f.relative_to(R/'source/kernel');dest.parent.mkdir(parents=True,exist_ok=True)
  assert not dest.is_symlink();shutil.copyfile(f,dest)
subprocess.run([str(K/'scripts/config'),'--file',str(O/'.config'),'--enable','CUSTOM_KERNEL_ACCELEROMETER','--enable','BMC156_ACC','--disable','MTK_BMA253','--disable','MTK_MC3416'],check=True)
base=['make','-C',str(K),'O='+str(O),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','-j1']
results=[]
for target in ['olddefconfig','prepare','drivers/misc/mediatek/sensors-1.0/']:
 cmd=base+[target];start=time.time()
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 log=target.replace('/','_')+'.log';(R/'evidence'/log).write_text(p.stdout)
 results.append(dict(command=cmd,exit=p.returncode,seconds=time.time()-start,log=log))
 print(target,'exit',p.returncode,p.stdout[-16000:] if p.returncode else p.stdout[-2000:],flush=True)
 (R/'evidence/kernel-build.json').write_text(json.dumps(results,indent=2)+'\n')
 if p.returncode:raise SystemExit(p.returncode)
