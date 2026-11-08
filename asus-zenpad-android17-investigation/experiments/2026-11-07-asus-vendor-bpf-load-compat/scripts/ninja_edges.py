from pathlib import Path
import json
A=Path('/srv/android/lineage24/out/soong');R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');found=[]
for p in sorted(A.glob('build.lineage_p00a.[0-9].ninja')):
 with p.open() as f:
  acc='';keep=False;chunk=[]
  for line in f:
   acc+=line
   if line.rstrip().endswith('$'):continue
   if acc.startswith('build '):
    if keep:found.append(''.join(chunk))
    keep='system/bpf/loader/libbpf_android/android_arm64_armv8-a_' in acc.split(':',1)[0];chunk=[]
   if keep:chunk.append(acc)
   acc=''
  if keep:found.append(''.join(chunk))
 if found:print('SHARD',p.name,flush=True);break
(R/'evidence/native-edges.json').write_text(json.dumps(found,indent=2));print('\n'.join(found)[:30000])
