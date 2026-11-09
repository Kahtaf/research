#!/usr/bin/env python3
"""Update only the known recovery capsule, after preserving its full preimage."""
from pathlib import Path
import fcntl,hashlib,json,os,stat
RUN=Path('/run/asus-alpine')
FOLDER=Path('/mnt/alpine-sd/2026-11-08-asus-alpine')
OLD='dac48be3cc2db22e2a099ef3948618f8561d737cc4bc2b49de14cd1ef5816cee'
BOOT='7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316'
BCB='e5a00aa9991ac8a5ee3109844d84a55583bd20572ad3ffcd42792f3c36b183ad'
SIZE=16740352
sha=lambda data:hashlib.sha256(data).hexdigest()
assert os.geteuid()==0 and os.uname().release=='3.18.35'
assert FOLDER.stat().st_dev==os.makedev(179,129)
assert (FOLDER/'ALPINE.ID').read_text()=='asus-alpine-stock-kernel-v1\n'
assert (FOLDER/'ROOT.EXT4.ENABLE').read_text()=='asus-alpine-ext4-root-v1\n'
assert (FOLDER/'alpine-root.ext4').stat().st_size==2147483648
assert json.loads((RUN/'sd-root-build.json').read_text())['phase']=='SEALED_CLEAN_AND_ENABLED'
manifest=json.loads((RUN/'sd-capsule-manifest.json').read_text())
assert manifest['kernel_wrapped_sha256']=='b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880'
assert manifest['kernel_byte_identical_to_original_boot'] and manifest['kernel_byte_identical_to_original_recovery']
assert manifest['sd_root_image_bytes']==2147483648
candidate=FOLDER/'recovery-sd-root-candidate.img'
assert stat.S_ISREG(candidate.lstat().st_mode)
image=candidate.read_bytes()
assert len(image)==SIZE and sha(image)==manifest['image_sha256']
def node(part,start,sectors):
 sys=Path('/sys/class/block',part)
 assert int((sys/'start').read_text())==start and int((sys/'size').read_text())==sectors
 major,minor=map(int,(sys/'dev').read_text().split(':'))
 path=Path('/dev','asus-update-'+part)
 if not path.exists():os.mknod(path,stat.S_IFBLK|0o600,os.makedev(major,minor))
 s=path.stat();assert stat.S_ISBLK(s.st_mode) and s.st_rdev==os.makedev(major,minor)
 return path
boot=node('mmcblk0p9',127488,32696)
rec=node('mmcblk0p10',160184,32696)
para=node('mmcblk0p12',225576,1024)
assert sha(boot.read_bytes())==BOOT
old=rec.read_bytes();assert len(old)==SIZE and sha(old)==OLD
with para.open('rb') as f:bcb=f.read(2048)
assert sha(bcb)==BCB and not any(bcb)
backup=FOLDER/('recovery-before-sd-root-'+OLD[:12]+'.img')
assert not backup.exists()
with backup.open('xb') as f:f.write(old);f.flush();os.fsync(f.fileno())
assert sha(backup.read_bytes())==OLD
receipt={'status':'PREIMAGE_SAVED_READY_TO_WRITE','old_recovery_sha256':OLD,'new_recovery_sha256':sha(image),'boot_sha256':BOOT,'bcb_sha256':BCB,'writes':'recovery p10 only','bytes':SIZE}
(RUN/'sd-capsule-update.json').write_text(json.dumps(receipt)+'\n');os.sync()
with rec.open('r+b',buffering=0) as f:
 view=memoryview(image)
 while view:
  n=f.write(view[:1048576]);assert n and n>0;view=view[n:]
 os.fsync(f.fileno())
os.sync()
# Drop the partition's cached buffers before the full read-back comparison.
with rec.open('rb',buffering=0) as f:fcntl.ioctl(f.fileno(),0x1261)
assert sha(rec.read_bytes())==sha(image),'Recovery read-back failed; preserved preimage is available'
assert sha(boot.read_bytes())==BOOT
with para.open('rb') as f:assert f.read(2048)==bcb
receipt['status']='RECOVERY_UPDATED_FULL_READBACK_VERIFIED_NO_REBOOT'
(RUN/'sd-capsule-update.json').write_text(json.dumps(receipt)+'\n')
with (FOLDER/'recovery-sd-update-receipt.json').open('x') as f:json.dump(receipt,f);f.write('\n');f.flush();os.fsync(f.fileno())
os.sync();print(json.dumps(receipt))
