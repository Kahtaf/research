from pathlib import Path
import subprocess,json
s=Path('/srv/android/lineage24')
for root in ['/srv/android','/srv/android/asus-android17','/srv/android/asus-bmc156-full-kernel-r1/export-compact']:
 p=Path(root);print(root, sorted(x.name for x in p.iterdir() if 'private' not in x.name and 'calibration' not in x.name) if p.exists() else 'absent')
for d in ['system/libvintf','kernel/configs']:
 p=s/d;print(d,subprocess.run(['git','-C',str(p),'rev-parse','HEAD'],capture_output=True,text=True).stdout)
 print(subprocess.run(['git','-C',str(p),'branch','-a'],capture_output=True,text=True).stdout[:4000])
print('ASSEMBLE',list((s/'system/libvintf').glob('**/*assemble*')))
print('BUILD',list((s/'hardware/interfaces/compatibility_matrices/build').glob('*')))
print('CONFIG BUILD',list((s/'kernel/configs/build').glob('*')))
