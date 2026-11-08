from pathlib import Path
import base64,datetime,hashlib,json,os,resource,subprocess
R=Path('/srv/android/asus-global-delay-budget-20261108');K=R/'kernel';O=R/'out';E=R/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((E/'preparation.json').read_text())['status']=='ISOLATED_SOURCE_PREPARED'
assert sha(O/'.config')=='01d6729f825798899e21192e6c33f96a80b47ccbedd5dc6cab10f78c1f9c7f31'
assert resource.getrlimit(resource.RLIMIT_AS)==(-1,-1)
for n in ['MAKEFLAGS','MFLAGS','KBUILD_OUTPUT','KCONFIG_CONFIG','LOCALVERSION','CROSS_COMPILE','KBUILD_BUILD_TIMESTAMP','KBUILD_BUILD_VERSION']:os.environ.pop(n,None)
os.environ['TMPDIR']=str(R/'tmp');os.environ['KBUILD_BUILD_VERSION']='1'
cmd=['make','-C',str(K),'O='+str(O),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','LOCALVERSION=-minplat','-j8','Image.gz-dtb']
rec=dict(command=cmd,kernel_invocations=1,helper_invocations=0,max_jobs=8,timeout=None,rlimit_as=list(resource.getrlimit(resource.RLIMIT_AS)),started=datetime.datetime.now(datetime.timezone.utc).isoformat())
with (E/'kernel-attempt.json').open('x') as f:json.dump(rec,f,indent=2)
with (E/'kernel-compile.log').open('x') as f:q=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
rec.update(exit=q.returncode,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),config_sha256=sha(O/'.config'))
(E/'kernel-status.json').write_text(json.dumps(rec,indent=2)+'\n')
if q.returncode==0:
 assert rec['config_sha256']=='01d6729f825798899e21192e6c33f96a80b47ccbedd5dc6cab10f78c1f9c7f31'
 rec['artifacts']={n:dict(bytes=(O/n).stat().st_size,sha256=sha(O/n)) for n in ['arch/arm64/boot/Image.gz-dtb','arch/arm64/boot/Image','.config','vmlinux','System.map','arch/arm64/boot/dts/mediatek/asus-p00a.dtb','include/generated/utsrelease.h','include/generated/compile.h']}
 (E/'build-receipt.json').write_text(json.dumps(rec,indent=2)+'\n')
files={}
for p in [E/'kernel-attempt.json',E/'kernel-status.json',E/'kernel-compile.log',E/'build-receipt.json']:
 if p.exists():
  d=p.read_bytes();files['evidence/'+p.name]=dict(data=base64.b64encode(d).decode(),sha256=hashlib.sha256(d).hexdigest())
print(json.dumps(dict(files=files,build=rec)))
