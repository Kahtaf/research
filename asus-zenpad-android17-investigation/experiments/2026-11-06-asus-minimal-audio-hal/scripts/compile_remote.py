from pathlib import Path
import os,resource,re,shlex,subprocess,json,hashlib,shutil
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
a=Path('/srv/android/lineage24');s=Path('/srv/android/asus-minimal-audio-hal-20261106');out=s/'out';out.mkdir(exist_ok=True)
variables={}
for line in (s/'evidence/tinyalsa-inputs.txt').read_text().splitlines():
 if ' = ' in line:
  k,v=line.split(' = ',1);variables[k]=v
 if line.endswith(' ='):variables[line[:-2]]=''
def expand(v):
 for i in range(20):
  new=re.sub(r'\$\{([^}]+)\}',lambda m:variables[m[1]],v)
  if new==v:return v.replace('$ ',' ')
  v=new
 raise ValueError('recursive variable')
edge=(s/'evidence/audio-default-commands.txt').read_text()
cflags=next(l.strip().split(' = ',1)[1] for l in edge.splitlines() if l.strip().startswith('cFlags ='))
flags=shlex.split(expand(cflags));flags=[x for x in flags if x not in ['-flto=thin','-fsplit-lto-unit']]
clang=a/expand('${g.android.soong.cc.config.ClangBin}')/'clang'
flags += ['-fno-lto','-I'+str(s/'src'),'-I'+str(s/'source/sdk37/external/tinyalsa_new/include')]
receipts=[]
def run(args):
 r=subprocess.run(list(map(str,args)),cwd=a,text=True,capture_output=True)
 receipts.append({'argv':list(map(str,args)),'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
 (out/'compile.json').write_text(json.dumps(receipts,indent=2)+'\n')
 print('RC',r.returncode,str(args[-1]));print(r.stderr[:6000])
 if r.returncode:raise SystemExit(r.returncode)
objects=[]
for name in ['audio_hw','transport','routes']:
 obj=out/(name+'.o');run([clang,*flags,'-MD','-MF',out/(name+'.d'),'-c',s/'src'/(name+'.c'),'-o',obj]);objects.append(obj)
# Build the actual tinyalsa v2 source in our own fixture. No active Ninja.
tiny=[]
for name in ['mixer','mixer_hw','mixer_plugin','pcm','pcm_hw','pcm_plugin','snd_card_plugin']:
 obj=out/('tiny_'+name+'.o');run([clang,*flags,'-Wno-macro-redefined','-MD','-MF',out/('tiny_'+name+'.d'),'-c',s/'source/sdk37/external/tinyalsa_new/src'/(name+'.c'),'-o',obj]);tiny.append(obj)
# Real Bionic/runtime inputs already built by SDK37, copied independently.
deps=[]
for rel in ['out/soong/.intermediates/bionic/libc/libc/android_vendor_arm64_armv8-a_shared/libc.so','out/soong/.intermediates/bionic/libdl/libdl/android_vendor_arm64_armv8-a_shared/libdl.so','out/soong/.intermediates/bionic/libm/libm/android_vendor_arm64_armv8-a_shared/libm.so','out/soong/.intermediates/bionic/libc/crtbegin_so/android_vendor_arm64_armv8-a/crtbegin_so.o','out/soong/.intermediates/bionic/libc/crtend_so/android_vendor_arm64_armv8-a/crtend_so.o']:
 p=a/rel
 if not p.is_file():raise SystemExit('MISSING REAL LINK INPUT '+str(p))
 dest=out/p.name;shutil.copyfile(p,dest);deps.append({'source':str(p),'copy':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
(out/'link-inputs.json').write_text(json.dumps(deps,indent=2)+'\n')
base=[clang,'-target','aarch64-linux-android37','-nostdlib','-shared','-fuse-ld=lld','-Wl,--no-undefined','-Wl,-z,relro,-z,now','-Wl,-z,noexecstack','-Wl,-z,max-page-size=4096','-Wl,--build-id=sha1',out/'crtbegin_so.o']
run([*base,*tiny,'-L'+str(out),'-lc','-ldl',out/'crtend_so.o','-Wl,-soname,libtinyalsav2.so','-o',out/'libtinyalsav2.so'])
run([*base,*objects,'-L'+str(out),'-ltinyalsav2','-lc',out/'crtend_so.o','-Wl,-soname,audio.primary.mt8163.so','-o',out/'audio.primary.mt8163.so'])
readelf=clang.parent/'llvm-readelf'
for elf in ['audio.primary.mt8163.so','libtinyalsav2.so']:
 r=subprocess.run([readelf,'-h','-d','--dyn-syms',out/elf],capture_output=True,text=True,check=True);(out/(elf+'.elf.txt')).write_text(r.stdout)
print('COMPLETE real SDK37 ARM64 compile/link, serial one CPU / 1GiB AS; no target execution')
