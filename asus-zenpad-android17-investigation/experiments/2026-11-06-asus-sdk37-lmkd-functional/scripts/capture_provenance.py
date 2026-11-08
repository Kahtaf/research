from pathlib import Path
import json,re,hashlib,subprocess as s,datetime
R=Path('/srv/android/asus-sdk37-lmkd-functional');A=Path('/srv/android/lineage24');E=R/'evidence'
# Freeze exact small build-edge blocks. No build command is executed.
F=A/'out/soong/build.lineage_p00a.7.ninja';blocks=[];block=[]
for line in F.open():
 if not line.strip():
  b=''.join(block)
  if 'module_name=lmkd;' in b and ('unstripped/lmkd' in b or '/obj/system/memory/lmkd/' in b):blocks.append(b)
  block=[]
 else:block.append(line)
(E/'lmkd-exact-build-blocks.ninja').write_text('\n\n'.join(blocks))
M=A/'out/soong/build.lineage_p00a.ninja';blocks=[];keep=False;block=[]
for line in M.open():
 if line.startswith(('rule ','pool ')):
  if keep:blocks.append(''.join(block))
  keep=bool(re.match(r'rule g.cc.(ld|cc|cxx|strip)\s',line));block=[]
 if keep:block.append(line)
 if keep and not line.strip():blocks.append(''.join(block));block=[];keep=False
(E/'native-rules.ninja').write_text('\n'.join(blocks))
# Pins for all selected daemon source inputs.
a=[]
for f in (R/'inputs/lmkd').rglob('*'):
 if f.is_file():a.append({'path':str(f.relative_to(R/'inputs')),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(E/'lmkd-source-manifest.json').write_text(json.dumps(a,indent=2))
# Expanded required pidfd implementation interfaces, matching both kernel source trees.
V=R/'kernel-memory-r1/source';P=Path('/srv/android/asus-bmc156-full-kernel-r1/kernel');paths=['include/uapi/asm-generic/unistd.h','include/linux/syscalls.h','kernel/signal.c','kernel/pid.c','include/linux/pid.h']
a=[]
for p in paths:
 def h(x):return hashlib.sha256(x.read_bytes()).hexdigest() if x.exists() else None
 a.append({'path':p,'virtual':h(V/p),'physical':h(P/p)})
(E/'pidfd-source-parity.json').write_text(json.dumps(a,indent=2));print('pidfd mismatches',[x for x in a if x['virtual']!=x['physical']])
