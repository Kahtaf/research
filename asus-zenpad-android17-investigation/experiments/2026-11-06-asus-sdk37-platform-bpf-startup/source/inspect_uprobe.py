from pathlib import Path
import subprocess as s
T=Path('/srv/android/lineage24')
p=T/'packages/modules/UprobeStats/bpfloader/UprobeStatsBpfLoad.cpp';print(p.read_text())
for d in ['out/target/product/p00a/apex/com.android.uprobestats/bin','out/soong/.intermediates/packages/modules/UprobeStats/bpfloader/uprobestatsbpfload']:
 p=T/d;print('PATH',p)
 if p.exists():
  for f in p.rglob('*'):
   if f.is_file() and f.name=='uprobestatsbpfload':print(f,f.stat().st_size)
