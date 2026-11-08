from pathlib import Path
import os,json,hashlib,subprocess as s,time
O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106');T=Path('/srv/android/lineage24');R=Path('/srv/android/asus-network-runtime');B=O/'build/postimage';B.mkdir(exist_ok=False)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.environ['TMPDIR']=str(O/'tmp');os.environ['PWD']='/proc/self/cwd'
cmd=json.loads((O/'inputs/prior/platform-build-legacy/command.json').read_text())['argv']
cmd=[a.replace(str(R/'platform-build-legacy/bpfloader.rs'),str(O/'artifacts/postimage/system/bpf/loader/bpfloader.rs')).replace(str(R/'platform-build-legacy/bpfloader'),str(B/'bpfloader')) for a in cmd]
(B/'bpfloader.clang.rsp').write_bytes((O/'inputs/prior/platform-build-legacy/bpfloader.clang.rsp').read_bytes())
# Every out/ input resolves inside the frozen snapshot; compiler executables are hash-pinned read-only inputs.
(B/'command.json').write_text(json.dumps({'argv':cmd,'cwd':str(O/'snapshot'),'cpu_affinity':list(os.sched_getaffinity(0)),'env':{'PWD':os.environ['PWD'],'TMPDIR':os.environ['TMPDIR']},'start_time':time.time()},indent=2)+'\n')
trace=['strace','-f','-qq','-e','trace=%file','-o',str(B/'file-access.strace')]
with (B/'build.log').open('w') as f:p=s.run(trace+cmd,cwd=O/'snapshot',stdout=f,stderr=s.STDOUT)
(B/'build.exit').write_text(str(p.returncode)+'\n')
if p.returncode:print((B/'build.log').read_text());raise SystemExit(p.returncode)
strip=T/'prebuilts/clang/host/linux-x86/clang-r584948b/bin/llvm-strip';q=s.run([str(strip),'-g',str(B/'bpfloader'),'-o',str(O/'artifacts/bpfloader-postimage')],capture_output=True,text=True);(B/'strip.log').write_text(q.stdout+q.stderr);assert q.returncode==0
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen=json.loads((O/'evidence/frozen-inputs.json').read_text());changed=[n for n,d in frozen.items() if h(O/n)!=d['sha256']];assert not changed,changed
result={'exit':p.returncode,'unstripped_sha256':h(B/'bpfloader'),'elf_sha256':h(O/'artifacts/bpfloader-postimage'),'source_sha256':h(O/'artifacts/postimage/system/bpf/loader/bpfloader.rs'),'prior_elf_sha256':h(O/'inputs/prior/artifacts/bpfloader-legacy'),'frozen_inputs_unchanged':True,'finish_time':time.time()}
(O/'evidence/build-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
