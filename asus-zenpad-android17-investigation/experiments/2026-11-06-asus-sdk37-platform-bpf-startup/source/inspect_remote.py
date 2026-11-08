from pathlib import Path
import subprocess,json
R=Path('/srv/android/asus-network-runtime');T=Path('/srv/android/lineage24')
print('NATIVE JOB STATE')
print(subprocess.run(['ps','-eo','pid,ppid,etime,stat,args'],capture_output=True,text=True).stdout)
for base in [R,R/'platform-build-legacy',R/'evidence',R/'inputs/platform-source',R/'run-r16']:
 print('DIRECTORY',str(base));print('\n'.join(str(p.relative_to(base)) for p in base.iterdir()) if base.exists() else 'MISSING')
for rel in ['patches/12-platform-ringbuf-selftest-minimum.patch','platform-build-legacy/command.json','platform-build-legacy/build.log','run-r16/result.json','run-r16/qemu-command.json']:
 p=R/rel; print('FILE',str(p));print(p.read_text() if p.exists() else 'MISSING')
