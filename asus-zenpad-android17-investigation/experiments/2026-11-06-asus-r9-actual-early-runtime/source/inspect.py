from pathlib import Path
import subprocess,json,os
R=Path('/srv/android/asus-r9-actual-early-runtime-20261106');R.mkdir(exist_ok=False);(R/'source').mkdir();(R/'evidence').mkdir();(R/'inputs').mkdir();(R/'tmp').mkdir()
G=Path('/srv/android/asus-genuine-service-runtime')
d={}
for n in ['qemu-img','qemu-nbd','nbdkit','guestfish','debugfs','fusermount','aarch64-linux-gnu-gcc']:
 p=subprocess.run(['which',n],capture_output=True,text=True);d[n]=p.stdout.strip()
for n in ['source/seed_exec.c','inputs/boot-r9/fstab.mt8163','inputs/boot-r9/root/system/etc/init/hw/firstboot-observer.rc','inputs/boot-r9/root/system/etc/init/firstboot-observer.rc','source/prepare_probe_r5.py']:
 p=G/n
 if p.is_file():d[n]=p.read_text()
for cmd in [['id'],['df','-T',str(R)],['sudo','-n','true']]:
 p=subprocess.run(cmd,capture_output=True,text=True);d[str(cmd)]={'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
print(json.dumps(d,indent=2));(R/'evidence/inspection.json').write_text(json.dumps(d,indent=2))
