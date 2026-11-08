from pathlib import Path
import subprocess as s
T=Path('/srv/android/lineage24');O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106')
for line in s.check_output(['ps','-eo','pid,ppid,etime,stat,rss,vsz,comm'],text=True).splitlines():
 if 'python3' in line:print(line)
print('GRAPH SIZES',[(p.name,p.stat().st_size) for p in (T/'out/soong').glob('build.lineage_p00a*.ninja')]);print('OWNED EVIDENCE',[(p.name,p.stat().st_size) for p in (O/'evidence').iterdir()])
for rel in ['packages/modules/UprobeStats/bpfloader/BpfLoader.cpp','packages/modules/UprobeStats/bpfloader/Android.bp','system/bpf/loader/Loader.cpp']:
 p=T/rel
 if p.exists():
  print('FILE',rel);print(p.read_text() if 'Uprobe' in rel else '\n'.join(l for l in p.read_text().splitlines() if any(k in l for k in ['location','/etc/bpf','exec','return','exit'])))
print('UPROBE SOURCE FILES',s.run(['find',str(T/'packages/modules/UprobeStats'),'-maxdepth','3','-iname','*loader*'],capture_output=True,text=True).stdout)
