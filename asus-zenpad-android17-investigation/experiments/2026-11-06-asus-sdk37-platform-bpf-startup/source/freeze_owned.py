from pathlib import Path
import os,subprocess as s,hashlib,json,shlex,shutil,time
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
R=Path('/srv/android/asus-network-runtime');T=Path('/srv/android/lineage24');O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106');O.mkdir(exist_ok=False)
for d in ['evidence','source','artifacts','inputs','snapshot','build','tmp']: (O/d).mkdir()
manifest={}
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,out):
 p=Path(p);out=O/out;out.parent.mkdir(parents=True,exist_ok=True)
 before=digest(p);shutil.copyfile(p,out);after=digest(p);assert before==after==digest(out),p
 manifest[str(out.relative_to(O))]={'source':str(p),'sha256':after,'bytes':out.stat().st_size}
 return out
patch=put(R/'patches/12-platform-ringbuf-selftest-minimum.patch','artifacts/12-platform-ringbuf-selftest-minimum.patch');assert digest(patch)=='2ffaf6c9349c06394d8d5e2e4e2bd70104725a2665f644dc0f1ae4f07988d502'
pre=put(T/'system/bpf/loader/bpfloader.rs','artifacts/preimage/system/bpf/loader/bpfloader.rs');assert digest(pre)==digest(R/'inputs/platform-source/bpfloader.rs')=='1548dffa03b5091bbb9b7cfcce92495ee2167f417e90b431117cf31ea77b4bd2'
post=put(pre,'artifacts/postimage/system/bpf/loader/bpfloader.rs')
p=s.run(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=post.parents[1],capture_output=True,text=True);(O/'evidence/patch-apply.log').write_text(p.stdout+p.stderr);assert p.returncode==0
assert digest(post)==digest(R/'platform-build-legacy/bpfloader.rs')=='babbccf603e600a2b77f5c71cbf6b1b978f72c176fd33bfab610ff2ba8956250'
# Postimage was deliberately changed after the copy; record its final hash.
manifest[str(post.relative_to(O))]['sha256']=digest(post);manifest[str(post.relative_to(O))]['bytes']=post.stat().st_size
for rel in ['evidence/platform-rust-command.txt','platform-build-legacy/command.json','platform-build-legacy/build.log','platform-build-legacy/bpfloader.clang.rsp','platform-build-legacy/bpfloader','artifacts/bpfloader-legacy','inputs/platform-bpfloader','run-r15/serial.log','run-r15/result.json','run-r15/inputs.json','run-r16/serial.log','run-r16/result.json','run-r16/inputs.json','run-r16/qemu-command.json','run-r16/guest_init.c','run-r16/init','source/seed_properties.cpp','source/network_loader.cpp','evidence/network_loader-compile-r11.log','evidence/platform-capture.json','handoff-r1/manifest.json','handoff-r1/network.config','handoff-r1/physical-baseline.config']:
 put(R/rel,'inputs/prior/'+rel)
for rel in ['system/bpf/loader/Android.bp','system/bpf/loader/Loader.cpp','system/bpfprogs/Android.bp','system/bpfprogs/progs.aconfig','out/target/product/p00a/product_packages.txt','out/target/product/p00a/.installable_files']:
 if (T/rel).is_file():put(T/rel,'inputs/actual/'+rel)
cmd=json.loads((R/'platform-build-legacy/command.json').read_text())['argv'];rsp=(R/'platform-build-legacy/bpfloader.clang.rsp').read_text();deps=set()
for i,a in enumerate(cmd):
 if a=='-L':
  d=Path(cmd[i+1])
  if str(d).startswith('prebuilts/'):continue
  for p in (T/d).iterdir():
   if p.is_file() and p.name.endswith(('.so','.rlib','.a','.rmeta')):deps.add(str(p.relative_to(T)))
 if a.startswith('force:') and '=' in a:deps.add(a.split('=',1)[1])
for a in shlex.split(rsp):
 if (T/a).is_file():deps.add(a)
for a in ['out/host/linux-x86/bin/soong_env','out/host/linux-x86/bin/rustc_wrapper','out/host/linux-x86/bin/rustc_linker']:
 deps.add(a)
for rel in sorted(deps):
 p=put(T/rel,'snapshot/'+rel);p.chmod((T/rel).stat().st_mode & 0o777)
# Compiler trees stay read-only external inputs, pinned below. No active out/ dependency remains.
for d in ['prebuilts/rust-toolchain','prebuilts/clang/host/linux-x86/clang-r584948b/bin']:
 p=O/'snapshot'/d;p.parent.mkdir(parents=True,exist_ok=True);p.symlink_to(T/d,target_is_directory=True)
# The builtins archive copied above is under a sibling path; don't overwrite it with a symlink.
tools=['prebuilts/rust-toolchain/linux-x86/1.93.1/bin/rustc','prebuilts/clang/host/linux-x86/clang-r584948b/bin/clang++','prebuilts/clang/host/linux-x86/clang-r584948b/bin/clang++-real','prebuilts/clang/host/linux-x86/clang-r584948b/bin/ld.lld','prebuilts/clang/host/linux-x86/clang-r584948b/bin/llvm-strip']
pins={}
for rel in tools:
 p=T/rel
 if p.exists():
  pins[rel]={'sha256':digest(p),'resolved':str(p.resolve()),'bytes':p.stat().st_size}
  q=s.run(['ldd',str(p)],capture_output=True,text=True);pins[rel]['ldd']=q.stdout+q.stderr
for p in (T/'prebuilts/rust-toolchain/linux-x86/1.93.1/lib').glob('*.so'):
 pins[str(p.relative_to(T))]={'sha256':digest(p),'bytes':p.stat().st_size}
(O/'evidence/toolchain-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
(O/'evidence/frozen-inputs.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'owned':str(O),'files':len(manifest),'bytes':sum(x['bytes'] for x in manifest.values()),'strace':shutil.which('strace'),'time':time.time()}))
