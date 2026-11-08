from pathlib import Path
import subprocess as s
for r in ['/srv/android/lineage24/out/host/linux-x86/bin','/srv/android/asus-root-enabled-incremental-r1/host-r2']:
 p=Path(r);print(r,[str(x) for x in p.glob('*erofs*')])
p=Path('/srv/android/lineage24/out/host/linux-x86/bin/fsck.erofs');
if p.exists():print(s.run([str(p),'--help'],capture_output=True,text=True).stdout,s.run([str(p),'--help'],capture_output=True,text=True).stderr)
p=Path('/srv/android/lineage24/out/host/linux-x86/bin/dump.erofs');
if p.exists():print(s.run([str(p),'--help'],capture_output=True,text=True).stdout,s.run([str(p),'--help'],capture_output=True,text=True).stderr)
