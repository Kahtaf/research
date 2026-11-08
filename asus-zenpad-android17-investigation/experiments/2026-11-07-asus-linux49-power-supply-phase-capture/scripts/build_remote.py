from pathlib import Path
import datetime,hashlib,json,os,resource,subprocess,traceback
R=Path('/srv/android/asus-linux49-power-supply-phase-capture-20261107-431dfb9c');B=Path('/srv/android/asus-linux49-work-dispatch-capture-20261107-b4702f9a');K=R/'kernel';O=R/'out';E=R/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(E/n).write_text(json.dumps(d,indent=2)+'\n')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
assert not (E/'build-status.json').exists(),'One complete kernel candidate only'
assert resource.getrlimit(resource.RLIMIT_AS)==(-1,-1)
config=(O/'.config').read_bytes();assert hashlib.sha256(config).hexdigest()=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
s=dict(status='running',started=now(),max_jobs=8,compile_attempts=1,rlimit_as=list(resource.getrlimit(resource.RLIMIT_AS)),build_timeout=None)
save('build-status.json',s)
try:
 for n in ['MAKEFLAGS','MFLAGS','KBUILD_OUTPUT','KCONFIG_CONFIG','LOCALVERSION','CROSS_COMPILE','KBUILD_BUILD_TIMESTAMP','KBUILD_BUILD_VERSION']:os.environ.pop(n,None)
 os.environ.update(TMPDIR=str(R/'tmp'),KBUILD_BUILD_TIMESTAMP=datetime.datetime.now(datetime.timezone.utc).strftime('%a %b %d %H:%M:%S UTC %Y'),KBUILD_BUILD_VERSION='1')
 cmd=['make','-C',str(K),'O='+str(O),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','LOCALVERSION=-g717bb3c9e13c-dirty','-j8','Image.gz-dtb']
 s['command']=cmd;save('build-status.json',s)
 with (E/'compile-1.log').open('w') as f:q=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 s['compile_exit']=q.returncode
 assert q.returncode==0,('Own capture compile error: preserve log and reconcile; no variant',q.returncode)
 assert (O/'.config').read_bytes()==config==(B/'out/.config').read_bytes()
 pins=json.loads((E/'source-pins.json').read_text())
 for n,v in pins.items():assert sha(K/n)==v['after'] and sha(B/'kernel'/n)==v['before']
 assert sha(B/'out/arch/arm64/boot/Image.gz-dtb')=='2d64022664c5ff61296446a41a55186f24247fe9287f03a0ca398a6c26e2e3ab'
 files=['arch/arm64/boot/Image.gz-dtb','arch/arm64/boot/Image','.config','System.map','vmlinux','include/generated/utsrelease.h','include/generated/compile.h']
 save('build-receipt.json',dict(artifacts={n:dict(bytes=(O/n).stat().st_size,sha256=sha(O/n)) for n in files},config_byte_identical=True,selected_original_sources_unchanged=True,old_kernel_artifact_unchanged=True,release=(O/'include/generated/utsrelease.h').read_text(),version=(O/'include/generated/compile.h').read_text(),physical_tested=False))
 s.update(status='complete',exit=0)
except BaseException as exc:
 s.update(status='failed',exit=1,error=repr(exc));traceback.print_exc()
finally:
 s['finished']=now();save('build-status.json',s)
raise SystemExit(s['exit'])
