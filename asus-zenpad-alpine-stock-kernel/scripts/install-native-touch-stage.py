#!/usr/bin/env python3
"""Enable only the staged, reviewed native input revision on the closed desktop."""
from pathlib import Path
import hashlib,json,os,stat
stage=Path('/run/asus-goodix/native-trial');sd=Path('/mnt/alpine-sd/2026-11-08-asus-alpine')
assert sd.stat().st_dev==os.makedev(179,129)
assert (sd/'ALPINE.ID').read_text()=='asus-alpine-stock-kernel-v1\n'
assert not Path('/tmp/.X11-unix/X0').exists()
assert Path('/etc/asus-goodix/automatic-keyboard').read_text()=='onboard-v1\n'
watchdog=json.loads((stage/'state.json').read_text());assert watchdog['phase']=='ARMED'
assert Path('/proc',str(watchdog['pid']),'cmdline').read_bytes().split(b'\0')[1]==b'/run/asus-goodix/native-trial/watchdog.py'
entries=json.loads((stage/'manifest.json').read_text())
expected={'asus-goodix-desktop':'/usr/local/bin/asus-goodix-desktop','asus-goodix-browser':'/usr/local/bin/asus-goodix-browser','goodix-native-input.py':'/usr/local/bin/goodix-native-input.py','asus-goodix-libinput.conf':'/etc/X11/asus-goodix-libinput.conf'}
assert set(entries)==set(expected)
backup=sd/'private/desktop-before-native-input';backup.mkdir(mode=0o700)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt={'old':{},'new':{},'operation':'SD OS native input overlay only'}
for name,entry in entries.items():
 assert entry['destination']==expected[name] and sha(stage/name)==entry['sha256']
 target=Path(entry['destination'])
 if target.exists():
  assert stat.S_ISREG(target.lstat().st_mode)
  original=backup/name
  with original.open('xb') as f:f.write(target.read_bytes());f.flush();os.fsync(f.fileno())
  receipt['old'][str(target)]=sha(target)
 else:receipt['old'][str(target)]=None
for name,entry in entries.items():
 target=Path(entry['destination']);temp=target.with_name(target.name+'.native-new')
 with temp.open('xb') as f:f.write((stage/name).read_bytes());f.flush();os.fsync(f.fileno())
 temp.chmod(0o644 if name.endswith('.conf') else 0o755);temp.replace(target)
 receipt['new'][str(target)]=sha(target)
marker=Path('/etc/asus-goodix/native-touch');assert not marker.exists()
with marker.open('x') as f:f.write('libinput-v1\n');f.flush();os.fsync(f.fileno())
(backup/'receipt.json').write_text(json.dumps(receipt)+'\n');os.sync()
print('NATIVE_INPUT_STAGED_AND_ENABLED; rollback watchdog armed')
