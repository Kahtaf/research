from pathlib import Path
import subprocess as s
p=Path('/srv/android/lineage24/system/bpf/loader/Android.bp');print(p.read_text())
p=Path('/srv/android/lineage24/system/bpf/loader/Loader.cpp');print('\n'.join(p.read_text().splitlines()[:90]))
base=Path('/srv/android/lineage24/out/soong/.intermediates/system/bpf');print(s.run(['find',str(base),'-maxdepth','4','-type','f','-name','*.rsp'],capture_output=True,text=True).stdout)
for p in Path('/srv/android/lineage24/out').glob('*.ninja'):print('NINJA',p)
