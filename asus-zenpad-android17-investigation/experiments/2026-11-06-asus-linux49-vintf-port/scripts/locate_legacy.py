from pathlib import Path
import subprocess
for root in ['/srv/android/reference-kernel','/srv/android/lineage24/kernel','/srv/android/asus-android17/kernel-bpf-fd/android','/srv/android/asus-android17/kernel-bpf-fd/kernel/configs','/srv/android/asus-bmc156-full-kernel-r1/kernel/android']:
 p=Path(root);print(root,sorted(x.name for x in p.iterdir()) if p.exists() else 'absent')
p=Path('/srv/android/lineage24/kernel/configs')
for args in [['rev-parse','--is-shallow-repository'],['log','-5','--format=%H %s']]:
 print(args,subprocess.run(['git','-C',str(p)]+args,capture_output=True,text=True,timeout=20).stdout)
for root in ['/srv/android/lineage24','/srv/android/reference-kernel','/srv/android/asus-android17/kernel-bpf-fd']:
 print(root,subprocess.run(['find',root,'-maxdepth','4','-type','f','-name','android-base*'],capture_output=True,text=True,timeout=20).stdout)
