from pathlib import Path
import subprocess,os,json,hashlib,datetime,shutil,traceback,resource
R=Path('/srv/android/asus-usb-retained-log-kernel-build-20261107');B=Path('/srv/android/asus-early-retained-kernel-probe-20261107');K=R/'kernel';O=R/'out';E=R/'evidence'
LOGGER='arch/arm64/kernel/asus_retained_trace.c'
PATCH_SHA='9d9790f13e837ab7569a706e790d99c372d69c3700e8767811723c0bdd0718fa'
BEFORE='15c4e2069326c7e2ecd2679240983913fc51122f5149be215e4707cb76de0a64';AFTER='8373baa301650d2bf3befe547df11a3079e22c51aec8a207de64eae0f1bb3348'
CONFIG='0fddb41316305c672b0afd0a64b2615c6dae3c5727f5ff4ead791272ff71b696'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save():(E/'build-status.json').write_text(json.dumps(record,indent=2)+'\n')
assert not K.exists() and not O.exists() and not (E/'build-status.json').exists(), 'Existing owned attempt refused'
record=dict(started=now(),pid=os.getpid(),status='preparing',max_jobs=8,affinity=sorted(os.sched_getaffinity(0)),rlimit_as=list(resource.getrlimit(resource.RLIMIT_AS)),commands=[])
save()
try:
 assert resource.getrlimit(resource.RLIMIT_AS)==(resource.RLIM_INFINITY,resource.RLIM_INFINITY)
 assert shutil.disk_usage(R).free>25*1024**3
 patch=R/'source/retained-linux-owned-initialization.patch';assert sha(patch)==PATCH_SHA
 original={str(p):sha(p) for p in [B/'kernel'/LOGGER,B/'out/.config',B/'out/arch/arm64/boot/Image.gz-dtb']}
 assert original[str(B/'kernel'/LOGGER)]==BEFORE
 assert (B/'out/.config').stat().st_size==126511 and original[str(B/'out/.config')]==CONFIG
 assert original[str(B/'out/arch/arm64/boot/Image.gz-dtb')]=='d94b26f4e806a0c86b28e42c7a8e7590bfefa96b5c91a50f3a80a05445c867b2'
 subprocess.run(['cp','-a',str(B/'kernel'),str(K)],check=True)
 O.mkdir();shutil.copyfile(B/'out/.config',O/'.config')
 assert sha(K/LOGGER)==BEFORE and (K/LOGGER).stat().st_ino!=(B/'kernel'/LOGGER).stat().st_ino
 cmd=['patch','--batch','--forward','--fuzz=0','-p1','-d',str(K),'-i',str(patch)]
 with (E/'patch.log').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 assert p.returncode==0,('patch',p.returncode)
 assert 'fuzz' not in (E/'patch.log').read_text().lower() and 'offset' not in (E/'patch.log').read_text().lower()
 assert sha(K/LOGGER)==AFTER
 (E/'changed-source-pins.json').write_text(json.dumps(dict(before={LOGGER:BEFORE},after={LOGGER:AFTER},patch_sha256=PATCH_SHA,patch_command=cmd,patch_exit=p.returncode,copy_method='cp -a; independent files, no hardlinks; fresh out/config/tmp',compile_corrections=[],no_full_tree_rehash=True),indent=2)+'\n')
 for name in ['MAKEFLAGS','MFLAGS','KBUILD_OUTPUT','KCONFIG_CONFIG','LOCALVERSION','CROSS_COMPILE','KBUILD_BUILD_TIMESTAMP','KBUILD_BUILD_VERSION']:os.environ.pop(name,None)
 os.environ['TMPDIR']=str(R/'tmp')
 os.environ['KBUILD_BUILD_TIMESTAMP']=datetime.datetime.now(datetime.timezone.utc).strftime('%a %b %d %H:%M:%S UTC %Y')
 os.environ['KBUILD_BUILD_VERSION']='1'
 cmd=['make','-C',str(K),'O='+str(O),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','LOCALVERSION=-g717bb3c9e13c-dirty','-j8','Image.gz-dtb']
 record.update(status='running',build_timestamp=os.environ['KBUILD_BUILD_TIMESTAMP']);row=dict(command=cmd,started=now());record['commands'].append(row);save()
 with (E/'Image.gz-dtb.log').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 row.update(exit=p.returncode,finished=now());record['compile_exit']=p.returncode;save()
 assert p.returncode==0,('Image.gz-dtb',p.returncode)
 assert (O/'.config').read_bytes()==(B/'out/.config').read_bytes() and sha(O/'.config')==CONFIG
 for n,h in original.items():assert sha(Path(n))==h,('baseline changed',n)
 assert sha(K/LOGGER)==AFTER
 (E/'original-selected-inputs.json').write_text(json.dumps(dict(before=original,after={n:sha(Path(n)) for n in original},unchanged=True,no_full_tree_rehash=True),indent=2)+'\n')
 artifacts={n:dict(bytes=(O/n).stat().st_size,sha256=sha(O/n)) for n in ['arch/arm64/boot/Image.gz-dtb','arch/arm64/boot/Image','.config','include/generated/utsrelease.h','include/generated/compile.h']}
 (E/'build-receipt.json').write_text(json.dumps(dict(artifacts=artifacts,release=(O/'include/generated/utsrelease.h').read_text(),version=(O/'include/generated/compile.h').read_text(),build_timestamp=record['build_timestamp'],original_inputs_unchanged=True,resolved_config_byte_identical=True,config_delta={},physical_tested=False),indent=2)+'\n')
 record.update(status='complete',exit=0)
except BaseException as exc:
 record.update(status='failed',exit=1,error=repr(exc));traceback.print_exc()
finally:
 record['finished']=now();save();print(json.dumps(record),flush=True)
raise SystemExit(record['exit'])
