#!/usr/bin/env python3
"""Seal only the owned, populated SD image and enable the reviewed root mode."""
from pathlib import Path
import hashlib,json,os,re,subprocess
run=Path('/run/asus-alpine');state=json.loads((run/'sd-root-build.json').read_text())
assert state['phase']=='POPULATED_AND_SELECTED_FILES_VERIFIED'
target=Path('/mnt/asus-root-stage');image=Path(state['image']);folder=image.parent
assert str(image)=='/mnt/alpine-sd/2026-11-08-asus-alpine/alpine-root.ext4.partial'
assert folder.stat().st_dev==os.makedev(179,129)
assert image.stat().st_size==2147483648 and not image.is_symlink()
assert os.path.ismount(target) and not (folder/'alpine-root.ext4').exists()
assert (folder/'ALPINE.ID').read_text()=='asus-alpine-stock-kernel-v1\n'
assert (folder/'PERSISTENCE.ENABLE').read_text()=='asus-alpine-state-v1\n'
assert (target/'root/.mozilla/asus-appliance/prefs.js').is_file()
assert (target/'root/asus-os-persistence-check.txt').is_file()
updates=json.loads(Path('/run/asus-alpine/stage-updates.json').read_text())
import base64
for name,data in updates.items():
 assert name in ('usr/local/bin/asus-goodix-desktop','usr/local/bin/asus-dashboard.py')
 dest=target/name;blob=base64.b64decode(data,validate=True)
 assert dest.is_file() and not dest.is_symlink()
 dest.write_bytes(blob);dest.chmod(0o755)
 assert hashlib.sha256(dest.read_bytes()).digest()==hashlib.sha256(blob).digest()
os.sync()
subprocess.run(['umount',str(target)],check=True)
subprocess.run(['losetup','-d',state['loop']],check=True)
check=subprocess.run(['e2fsck','-f','-p',str(image)])
assert check.returncode in (0,1),check.returncode
header=subprocess.check_output(['dumpe2fs','-h',str(image)],text=True,stderr=subprocess.DEVNULL)
assert set(re.search(r'^Filesystem features:\s*(.*)$',header,re.M)[1].split())==set(state['features'])
assert re.search(r'^Filesystem state:\s+clean$',header,re.M)
image.rename(folder/'alpine-root.ext4')
for name,value in [('ROOT.EXT4.ENABLE','asus-alpine-ext4-root-v1\n'),('GUI.ENABLE','asus-alpine-desktop-v1\n')]:
 path=folder/name
 assert not path.exists() and not path.is_symlink()
 with path.open('x') as f:f.write(value);f.flush();os.fsync(f.fileno())
os.sync()
state.update(phase='SEALED_CLEAN_AND_ENABLED',image=str(folder/'alpine-root.ext4'),filesystem_check_exit=check.returncode)
(run/'sd-root-build.json').write_text(json.dumps(state)+'\n')
print('SD_ROOT_SEALED_CLEAN_2GIB; original card layout and other folders untouched')
