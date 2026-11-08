import os,resource,pathlib,json,hashlib,subprocess
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(120,120))
P=pathlib.Path;R=P('/srv/android/asus-sdk37-system-ext4-qualification-20261106');plan=json.loads(P('/srv/android/asus-reviewed-build-kit/r8/inputs/plan.json').read_text());A=P(plan['aosp']);O=P(plan['product_out']);K=P('/srv/android/asus-sdk37-lmkd-functional/kernel-memory-r1');B=P(plan['compiled_fixture']);d={'files':{},'ext4_source_parity':[],'dependencies':{}}
def cap(p):
 p=P(p)
 if not p.exists():d['files'][str(p)]={'missing':True};return
 b=p.read_bytes();d['files'][str(p)]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 if len(b)<500000 and (p.suffix in ['.conf','.bp','.txt','.c','.h'] or p.name in ['.config']):d['files'][str(p)]['text']=b.decode(errors='replace')
for p in [A/'system/extras/ext4_utils/mke2fs.conf',A/'system/extras/ext4_utils/Android.bp',O/'obj/PACKAGING/system_intermediates/system_image_info.txt',A/'out/soong/.intermediates/system/extras/ext4_utils/mkuserimg_mke2fs/linux_glibc_x86_64/mkuserimg_mke2fs',K/'out/.config',B.parent/'out/.config',K/'out/arch/arm64/boot/Image',K/'source/fs/ext4/ext4.h',K/'source/fs/ext4/super.c',A/'external/e2fsprogs/misc/mke2fs.c',A/'external/e2fsprogs/contrib/android/e2fsdroid.c']:
 cap(p)
for p in sorted((K/'source/fs/ext4').rglob('*')):
 if p.is_file():
  rel=p.relative_to(K/'source');q=B/rel;h=hashlib.sha256(p.read_bytes()).hexdigest();qh=hashlib.sha256(q.read_bytes()).hexdigest() if q.exists() else None;d['ext4_source_parity'].append({'path':str(rel),'virtual':h,'physical':qh,'equal':h==qh})
for n in ['mke2fs','e2fsdroid','e2fsck','simg2img','debugfs']:
 p=A/'out/host/linux-x86/bin'/n
 d['dependencies'][n]=subprocess.run(['ldd',str(p)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=15).stdout
# Exact graph producing wrapper, from Soong graph. Capture only short matching producer stanza.
graph=A/'out/soong/build.ninja';target='out/soong/.intermediates/system/extras/ext4_utils/mkuserimg_mke2fs/linux_glibc_x86_64/mkuserimg_mke2fs'
d['soong_producer']=[]
if graph.exists():
 with graph.open() as f:
  active=False
  for line in f:
   if line.startswith('build '):active=line.startswith('build '+target+':')
   if active:d['soong_producer'].append(line.rstrip())
(R/'inspection2.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
