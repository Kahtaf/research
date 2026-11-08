from pathlib import Path
import subprocess,os,json,hashlib,datetime,shutil,fcntl
R=Path('/srv/android/asus-bmc156-full-kernel-r1');K=R/'kernel';O=R/'out';E=R/'evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def cfg(p):
 d={}
 for l in p.read_text().splitlines():
  if l.startswith('CONFIG_'):k,v=l.split('=',1);d[k]=v
  elif l.startswith('# CONFIG_') and l.endswith(' is not set'):d[l.split()[1]]='n'
 return d
assert R.resolve()==R and K.resolve()==K and O.resolve()==O
assert (E/'reconstruction.json').is_file() and shutil.disk_usage(R).free>30*1024**3
lock=(E/'build.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not (E/'build-status.json').exists(),'Existing attempt: inspect, never blindly restart'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(10)
os.environ['TMPDIR']=str(R/'tmp')
for name in ['MAKEFLAGS','MFLAGS','KBUILD_OUTPUT','KCONFIG_CONFIG','LOCALVERSION','CROSS_COMPILE']:os.environ.pop(name,None)
record=dict(started=now(),pid=os.getpid(),status='running',affinity=sorted(os.sched_getaffinity(0)),max_jobs=1,commands=[])
def save():(E/'build-status.json').write_text(json.dumps(record,indent=2)+'\n')
save()
try:
 subprocess.run([str(K/'scripts/config'),'--file',str(O/'.config'),'--enable','CUSTOM_KERNEL_ACCELEROMETER','--enable','BMC156_ACC','--disable','MTK_BMA253','--disable','MTK_MC3416'],check=True)
 base=['make','-C',str(K),'O='+str(O),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','LOCALVERSION=-g717bb3c9e13c-dirty','-j1']
 tool={}
 for n in ['aarch64-linux-gnu-gcc','aarch64-linux-gnu-ld','gcc','make']:
  p=Path(shutil.which(n)).resolve();tool[n]=dict(path=str(p),sha256=sha(p),version=subprocess.check_output([n,'--version'],text=True).splitlines()[0])
 (E/'toolchains.json').write_text(json.dumps(tool,indent=2)+'\n')
 for target in ['olddefconfig','Image.gz-dtb']:
  cmd=base+[target];row=dict(command=cmd,started=now());record['commands'].append(row);save()
  with (E/(target+'.log')).open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
  row.update(exit=p.returncode,finished=now());save()
  if p.returncode:raise RuntimeError(f'{target} exit {p.returncode}')
  if target=='olddefconfig':
   old=cfg(E/'physical-r5.config');new=cfg(O/'.config');delta={k:{'before':old.get(k,'n'),'after':new.get(k,'n')} for k in old.keys()|new.keys() if old.get(k,'n')!=new.get(k,'n')}
   assert delta=={'CONFIG_CUSTOM_KERNEL_ACCELEROMETER':{'before':'n','after':'y'},'CONFIG_BMC156_ACC':{'before':'n','after':'y'},'CONFIG_MTK_BMA253':{'before':'y','after':'n'},'CONFIG_MTK_MC3416':{'before':'y','after':'n'}},delta
   assert sha(O/'.config')=='10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2'
   (E/'config-delta.json').write_text(json.dumps(delta,sort_keys=True,indent=2)+'\n')
 record['status']='complete';record['exit']=0
except Exception as e:
 record['status']='failed';record['exit']=1;record['error']=repr(e)
finally:
 record['finished']=now();save()
raise SystemExit(record['exit'])
