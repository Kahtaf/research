from pathlib import Path
import subprocess,os,json,hashlib,datetime,resource,traceback
R=Path('/srv/android/asus-linux49-entry-text-r2-build-20261107');K=R/'kernel';O=R/'out';E=R/'evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,v):(E/n).write_text(json.dumps(v,indent=2)+'\n')
assert not (E/'build-status.json').exists(), 'One complete build only'
assert resource.getrlimit(resource.RLIMIT_AS)==(-1,-1)
config=(O/'.config').read_bytes();assert hashlib.sha256(config).hexdigest()=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
record=dict(status='running',started=now(),rlimit_as=list(resource.getrlimit(resource.RLIMIT_AS)),max_jobs=8,compile_attempts=1,supervisor_timeout=None)
save('build-status.json',record)
try:
 for n in ['MAKEFLAGS','MFLAGS','KBUILD_OUTPUT','KCONFIG_CONFIG','LOCALVERSION','CROSS_COMPILE','KBUILD_BUILD_TIMESTAMP','KBUILD_BUILD_VERSION']:os.environ.pop(n,None)
 os.environ['TMPDIR']=str(R/'tmp');os.environ['KBUILD_BUILD_TIMESTAMP']=datetime.datetime.now(datetime.timezone.utc).strftime('%a %b %d %H:%M:%S UTC %Y');os.environ['KBUILD_BUILD_VERSION']='1'
 cmd=['make','-C',str(K),'O='+str(O),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','LOCALVERSION=-g717bb3c9e13c-dirty','-j8','Image.gz-dtb']
 record.update(command=cmd,build_timestamp=os.environ['KBUILD_BUILD_TIMESTAMP']);save('build-status.json',record)
 with (E/'Image.gz-dtb.log').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 record['compile_exit']=p.returncode
 assert p.returncode==0,('Compile error; preserve and STOP, no rebuild',p.returncode)
 assert (O/'.config').read_bytes()==config
 receipt=dict(artifacts={n:dict(bytes=(O/n).stat().st_size,sha256=sha(O/n)) for n in ['arch/arm64/boot/Image.gz-dtb','arch/arm64/boot/Image','.config','System.map','vmlinux','include/generated/utsrelease.h','include/generated/compile.h']},release=(O/'include/generated/utsrelease.h').read_text(),version=(O/'include/generated/compile.h').read_text(),config_byte_identical=True,physical_tested=False)
 save('build-receipt.json',receipt);record.update(status='complete',exit=0)
except BaseException as exc:
 record.update(status='failed',exit=1,error=repr(exc));traceback.print_exc()
finally:
 record['finished']=now();save('build-status.json',record);print(json.dumps(record),flush=True)
raise SystemExit(record['exit'])
