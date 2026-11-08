from pathlib import Path
import base64,datetime,hashlib,json,os,resource,subprocess
R=Path('/srv/android/asus-minimal-platform-build-r3-20261108');K=R/'kernel';O=R/'out';E=R/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((E/'final-config-gate.json').read_text())['status']=='FINAL_CONFIG_GATE_PASS'
assert sha(O/'.config')==json.loads((E/'final-config-gate.json').read_text())['resolved_sha256']
assert not (E/'kernel-attempt.json').exists(),'ONE Image build only'
assert resource.getrlimit(resource.RLIMIT_AS)==(-1,-1),'No inherited address-space cap'
for n in ['MAKEFLAGS','MFLAGS','KBUILD_OUTPUT','KCONFIG_CONFIG','LOCALVERSION','CROSS_COMPILE','KBUILD_BUILD_TIMESTAMP','KBUILD_BUILD_VERSION']:os.environ.pop(n,None)
os.environ['TMPDIR']=str(R/'tmp');os.environ['KBUILD_BUILD_VERSION']='1'
cmd=['make','-C',str(K),'O='+str(O),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','LOCALVERSION=-minplat','-j8','Image.gz-dtb']
record=dict(command=cmd,attempts_this_continuation=1,total_kernel_invocations_in_experiment=3,initial_compile_and_r2_link_failures_preserved=True,helper_compilations_this_continuation=0,max_jobs=8,started=datetime.datetime.now(datetime.timezone.utc).isoformat(),timeout=None,rlimit_as=list(resource.getrlimit(resource.RLIMIT_AS)))
with (E/'kernel-attempt.json').open('x') as f:json.dump(record,f,indent=2)
with (E/'kernel-compile.log').open('w') as f:q=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
record.update(exit=q.returncode,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='complete' if q.returncode==0 else 'failed')
(E/'kernel-status.json').write_text(json.dumps(record,indent=2)+'\n')
files={}
if q.returncode==0:
 assert sha(O/'.config')==json.loads((E/'final-config-gate.json').read_text())['resolved_sha256']
 artifacts={n:dict(bytes=(O/n).stat().st_size,sha256=sha(O/n)) for n in ['arch/arm64/boot/Image.gz-dtb','arch/arm64/boot/Image','.config','vmlinux','System.map','arch/arm64/boot/dts/mediatek/asus-p00a.dtb','include/generated/utsrelease.h','include/generated/compile.h']}
 receipt=dict(**record,artifacts=artifacts,release=(O/'include/generated/utsrelease.h').read_text(),version=(O/'include/generated/compile.h').read_text())
 (E/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 for n in ['build-receipt.json','kernel-attempt.json','kernel-status.json']:
  p=E/n;d=p.read_bytes();files['evidence/'+n]=dict(data=base64.b64encode(d).decode(),sha256=hashlib.sha256(d).hexdigest())
log=E/'kernel-compile.log';summary=dict(bytes=log.stat().st_size,sha256=sha(log),tail=log.read_text(errors='replace').splitlines()[-65:])
(E/'kernel-log-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
for n in ['kernel-log-summary.json','kernel-status.json']:
 p=E/n;d=p.read_bytes();files['evidence/'+n]=dict(data=base64.b64encode(d).decode(),sha256=hashlib.sha256(d).hexdigest())
print(json.dumps(dict(files=files,status=record,log_summary=summary)))
