from pathlib import Path
import os,resource,subprocess,json,time,hashlib,signal,base64,re,shutil
R=Path('/srv/android/asus-stock-gpio28-review-20261106-r1');K=R/'kernel';O=R/'out';E=R/'evidence';B=Path('/srv/android/asus-bmc156-full-kernel-r1')
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(120,120));signal.alarm(240)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(10)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert all(json.loads((E/(n+'.json')).read_text())['exit']==0 for n in ['olddefconfig','arm64-codec','arm64-gpio','arm64-afe','board-dtb'])
(R/'inputs/tests/mtk-boundary.c').write_bytes(base64.b64decode(BOUNDARY))
assert sha(K/'drivers/pinctrl/mediatek/pinctrl-mtk-common.c')=='5f89c2ac60807673a0a165bf26b6019c1a21274b875053257ff6f39b472f4189'
platform=(K/'drivers/pinctrl/mediatek/pinctrl-mt8163.c').read_text().split('static const struct mtk_pinctrl_devdata mt8163_pinctrl_data = {')[1].split('\n};')[0]
assert '.pin_dir_grps' not in platform and '.pin_dout_grps' not in platform
(E/'mt8163-platform-data.txt').write_text(platform)
def limit():
 resource.setrlimit(resource.RLIMIT_CPU,(45,45));resource.setrlimit(resource.RLIMIT_FSIZE,(128*1024**2,128*1024**2));os.setsid()
def run(cmd,name):
 assert not (E/(name+'.json')).exists()
 start=time.time()
 with (E/(name+'.log')).open('wb') as f:
  p=subprocess.Popen([str(x) for x in cmd],cwd=R,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit)
  try:code=p.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();code='WALL_TIMEOUT'
 row=dict(command=[str(x) for x in cmd],exit=code,wall_seconds=time.time()-start,cpu_limit_seconds=45,wall_limit_seconds=60,affinity=sorted(os.sched_getaffinity(0)),rlimit_as=resource.getrlimit(resource.RLIMIT_AS))
 (E/(name+'.json')).write_text(json.dumps(row,indent=2)+'\n')
 print(name,code,flush=True)
 assert code==0,(E/(name+'.log')).read_text()[-4000:]
run(['gcc','-std=gnu89','-O0','-g','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-Wno-declaration-after-statement','-fsanitize=undefined','-fno-sanitize-recover=all',R/'inputs/tests/mtk-boundary.c','-o',R/'tmp/mtk-boundary-host'],'mtk-boundary-compile')
run([R/'tmp/mtk-boundary-host'],'mtk-boundary-run')
A=R/'artifacts';A.mkdir()
paths=['sound/soc/mediatek/mt_soc_audio_8163/'+n for n in ['mt_soc_codec_63xx.o','AudDrv_Gpio.o','AudDrv_Afe.o']]+['arch/arm64/boot/dts/mediatek/asus-p00a.dtb']
for rel in paths:
 p=O/rel;q=A/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 cmd=p.with_name('.'+p.name+'.cmd');assert cmd.exists();shutil.copyfile(cmd,q.with_name(cmd.name))
 if p.suffix=='.o':
  data=p.read_bytes();assert data[:4]==b'\x7fELF' and data[4]==2 and int.from_bytes(data[18:20],'little')==183 and int.from_bytes(data[16:18],'little')==1
  for tool,args in [('readelf',['-h']),('nm',[]),('objdump',['-dr'])]:
   run(['aarch64-linux-gnu-'+tool]+args+[p],p.stem+'-'+tool)
for rel in ['.config','include/config/auto.conf','include/generated/autoconf.h','include/generated/utsrelease.h','include/generated/uapi/linux/version.h','arch/arm64/include/generated/asm/asm-offsets.h','include/generated/bounds.h']:
 p=O/rel
 if p.exists():
  q=A/'kbuild-inputs'/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
# Retain complete dependency files and dtc command/source intermediates when present.
for p in (O/'arch/arm64/boot/dts/mediatek').glob('*asus-p00a*'):
 if p.is_file() and p.suffix!='.dtb':shutil.copyfile(p,A/p.name)
run([O/'scripts/dtc/dtc','-I','dtb','-O','dts','-o',A/'asus-p00a.decompiled.dts',O/'arch/arm64/boot/dts/mediatek/asus-p00a.dtb'],'dtb-decompile')
# Independent real preprocessor using the same source/include closure for a retained receipt.
run(['aarch64-linux-gnu-gcc','-E','-Wp,-MD,'+str(A/'asus-p00a.dts.d'),'-nostdinc','-undef','-D__DTS__','-x','assembler-with-cpp','-I',K/'arch/arm64/boot/dts','-I',K/'include',K/'arch/arm64/boot/dts/mediatek/asus-p00a.dts','-o',A/'asus-p00a.preprocessed.dts'],'dtb-source-preprocess')
post=json.loads((E/'candidate-source-manifest.json').read_text())
assert all(sha(K/n)==h for n,h in post.items())
# Rehash original BMC inputs only; no original build lifecycle/process inspection.
base=json.loads((E/'baseline-source-manifest.json').read_text())
assert all(sha(B/'kernel'/n)==h for n,h in base.items())
assert sha(B/'out/.config')=='10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2'
assert sha(B/'out/arch/arm64/boot/Image.gz-dtb')=='e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1'
assert not list(O.glob('arch/arm64/boot/Image*')) and not (O/'vmlinux').exists()
size=sum(p.stat().st_size for p in R.rglob('*') if p.is_file());allocated=sum(p.stat().st_blocks*512 for p in R.rglob('*') if p.is_file());assert max(size,allocated)<4*1024**3
rec=dict(arm64_relocatable_objects=paths[:3],dtb=paths[3],candidate_sources_unchanged_since_replay=True,all_62228_original_BMC_sources_unchanged=True,original_image_and_config_unchanged=True,no_full_image_or_vmlinux=True,owned_logical_bytes=size,owned_allocated_file_bytes=allocated,affinity=sorted(os.sched_getaffinity(0)),rlimit_as=resource.getrlimit(resource.RLIMIT_AS),hard_tree_memory_cap=False,memory_scope='1GiB RLIMIT_AS inherited per process, serial -j1; no aggregate cgroup memory cap claim',children_peak_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,artifacts={str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in A.rglob('*') if p.is_file()})
(E/'final-verification.json').write_text(json.dumps(rec,indent=2)+'\n')
print(json.dumps(rec,indent=2))
