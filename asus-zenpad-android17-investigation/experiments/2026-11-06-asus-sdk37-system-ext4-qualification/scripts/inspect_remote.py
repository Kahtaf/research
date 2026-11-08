import os, resource, json, hashlib, pathlib, subprocess
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(120,120))
P=pathlib.Path
R=P('/srv/android/asus-sdk37-system-ext4-qualification-20261106');R.mkdir()
planpath=P('/srv/android/asus-reviewed-build-kit/r8/inputs/plan.json');plan=json.loads(planpath.read_text());A=P(plan['aosp']);D=P(plan['device']);O=P(plan['product_out'])
result={'remote_root':str(R),'plan_sha256':hashlib.sha256(planpath.read_bytes()).hexdigest(),'resolved':{k:plan[k] for k in ['aosp','device','product_out','compiled_fixture']},'files':{},'graph':{},'tools':{}}
def capture(p):
 p=P(p)
 if p.exists():
  b=p.read_bytes();result['files'][str(p)]={'sha256':hashlib.sha256(b).hexdigest(),'text':b.decode(errors='replace')}
 else:result['files'][str(p)]={'missing':True}
for p in [D/'BoardConfig.mk',D/'rootdir/fstab.mt8163',A/'system/extras/ext4_utils/mkuserimg_mke2fs.py',A/'external/e2fsprogs/mke2fs.conf',A/'external/e2fsprogs/misc/mke2fs.conf.in',A/'build/make/tools/releasetools/build_image.py',O/'obj/PACKAGING/systemimage_intermediates/system_image_info.txt']:
 capture(p)
for p in (A/'out').glob('*.ninja'):
 hits=[]
 with p.open() as f:
  for line in f:
   if ('system.img' in line and ('build ' in line or 'build_image' in line)) or ('mkuserimg_mke2fs' in line and ('command =' in line or 'build ' in line)):
    hits.append(line.rstrip())
 result['graph'][str(p)]={'bytes':p.stat().st_size,'hits':hits}
for n in ['mkuserimg_mke2fs','mke2fs','e2fsdroid','e2fsck','tune2fs','simg2img','debugfs']:
 p=A/'out/host/linux-x86/bin'/n
 result['tools'][str(p)]={'exists':p.exists(),'resolved':str(p.resolve())}
 if p.exists():result['tools'][str(p)]['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
for n in ['qemu-system-aarch64','aarch64-linux-gnu-gcc','e2fsck']:
 import shutil
 result['tools'][n]=shutil.which(n)
(R/'inspection.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
