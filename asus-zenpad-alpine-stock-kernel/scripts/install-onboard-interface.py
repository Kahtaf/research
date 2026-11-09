#!/usr/bin/env python3
"""Promote the reviewed desktop helpers after preserving the closed GUI setup."""
from pathlib import Path
import hashlib,json,os,stat,subprocess
stage=Path('/run/asus-goodix/onboard-stage')
folder=Path('/mnt/alpine-sd/2026-11-08-asus-alpine')
assert os.uname().release=='3.18.35' and folder.stat().st_dev==os.makedev(179,129)
assert (folder/'ALPINE.ID').read_text()=='asus-alpine-stock-kernel-v1\n'
assert Path('/run/asus-alpine/root-mode').read_text().strip()=='SD-loop'
assert not Path('/tmp/.X11-unix/X0').exists(),'Stop the owned desktop first'
for p in Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try:args=(p/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,ProcessLookupError):continue
 assert not (args and b'firefox' in args[0] and b'/root/.mozilla/asus-appliance' in args),'Owner browser still running'
manifest=json.loads((stage/'manifest.json').read_text())
expected={name:'/usr/local/bin/'+name for name in ('asus-goodix-desktop','asus-goodix-browser','asus-goodix-keyboard','asus-goodix-osk')}
expected['recovery-start-desktop.sh']='/etc/asus-alpine/start-desktop'
assert set(manifest)==set(expected)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,entry in manifest.items():
 assert entry['destination']==expected[name]
 assert stat.S_ISREG((stage/name).lstat().st_mode)
 assert sha(stage/name)==entry['sha256']
binary=Path('/usr/local/bin/asus-jwm')
assert binary.is_file() and not binary.is_symlink()
version=subprocess.check_output([str(binary),'-v'],text=True)
assert 'JWM v2.4.6' in version
for option in ('confirm','icons','jpeg','nls','pango','png','shape','svg','xbm','xft','xinerama','xpm','xrender'):
 assert option in version.split(),option
backup=folder/'private/desktop-before-onboard';backup.mkdir(mode=0o700)
receipt={'status':'BACKED_UP_READY_TO_PROMOTE','old':{},'new':{},'packaged_jwm_sha256':sha(Path('/usr/bin/jwm')),'candidate_jwm_sha256':sha(binary)}
for name,path in expected.items():
 source=Path(path)
 if source.exists():
  assert stat.S_ISREG(source.lstat().st_mode)
  target=backup/name
  with target.open('xb') as f:f.write(source.read_bytes());f.flush();os.fsync(f.fileno())
  target.chmod(0o600);receipt['old'][path]=sha(source)
 else:receipt['old'][path]=None
for name,entry in manifest.items():
 dest=Path(entry['destination']);temp=dest.with_name(dest.name+'.onboard-new')
 with temp.open('xb') as f:f.write((stage/name).read_bytes());f.flush();os.fsync(f.fileno())
 temp.chmod(0o755);temp.replace(dest)
 assert sha(dest)==entry['sha256'];receipt['new'][str(dest)]=sha(dest)
for name,value in [('automatic-keyboard','onboard-v1\n'),('jwm-workarea','jwm-2.4.6-workarea-v1\n')]:
 dest=Path('/etc/asus-goodix',name)
 assert not dest.exists() and not dest.is_symlink()
 with dest.open('x') as f:f.write(value);f.flush();os.fsync(f.fileno())
receipt['status']='PROMOTED_NOT_STARTED; packaged JWM preserved'
assert sha(Path('/usr/bin/jwm'))==receipt['packaged_jwm_sha256']
(backup/'receipt.json').write_text(json.dumps(receipt)+'\n')
os.sync();print(json.dumps(receipt))
