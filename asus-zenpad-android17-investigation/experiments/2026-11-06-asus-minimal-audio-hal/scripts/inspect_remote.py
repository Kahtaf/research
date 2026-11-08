from pathlib import Path
import hashlib,json,os
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
a=Path('/srv/android/lineage24'); k=Path('/srv/android/asus-build-continuation/kernel')
print('KERNEL',list(k.glob('sound/soc/mediatek/*8163*')))
for p in Path('/srv/android/asus-hardware-completeness-audit/public-selected').rglob('*'):
 if p.is_file() and ('audio' in p.name.lower() or 'Audio' in str(p)):print('STOCK',p,p.stat().st_size)
for p in [a/'out/soong/build.ninja',a/'out/combined-aosp_p00a.ninja']:
 print('BUILD',p,p.exists())
 if p.exists():
  lines=p.open(); count=0
  for line in lines:
   if ('audio.primary.default' in line or '/libtinyalsa/' in line) and line.startswith('build '):
    print(line.rstrip());count+=1
    if count>=8:break
for d in ['prebuilts/clang/host/linux-x86','out/host/linux-x86/bin','out/target/product/p00a/vendor/lib64','out/target/product/p00a/system/lib64']:
 p=a/d
 print('FILES',d,[x.name for x in p.glob('*') if ('clang' in x.name or x.name in ['checkvintf','assemble_vintf','host_init_verifier','secilc','checkpolicy','libtinyalsa.so','libc.so','libdl.so','libm.so'])])
