#!/usr/bin/env python3
"""Show Linux selection, or clear only its known BCB command to return to stock."""
from pathlib import Path
import argparse,hashlib,json,os,stat,subprocess,uuid
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--return-to-stock',action='store_true')
p.add_argument('--reboot',action='store_true')
a=p.parse_args()
if a.reboot and not a.return_to_stock:p.error('--reboot requires --return-to-stock')
assert os.geteuid()==0 and os.uname().release=='3.18.35'
assert Path('/etc/asus-alpine-ram-release').read_text().strip()=='asus-alpine-stock-kernel-v1'
def device(part,start,sectors):
 sys=Path('/sys/class/block',part)
 assert int((sys/'start').read_text())==start and int((sys/'size').read_text())==sectors
 mm=tuple(map(int,(sys/'dev').read_text().split(':')))
 node=Path('/dev',part);s=node.stat()
 assert stat.S_ISBLK(s.st_mode) and s.st_rdev==os.makedev(*mm)
 return node
boot=device('mmcblk0p9',127488,32696)
assert hashlib.sha256(boot.read_bytes()).hexdigest()=='7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316'
para=device('mmcblk0p12',225576,1024)
with para.open('rb') as f:before=f.read(2048)
linux=b'boot-recovery'+bytes(2048-len(b'boot-recovery'))
stock=bytes(2048)
assert before in (linux,stock),'Unknown BCB contents; no bytes changed'
changed=False
if a.return_to_stock and before==linux:
 folder=Path('/mnt/alpine-sd/2026-11-08-asus-alpine')
 assert folder.stat().st_dev==os.makedev(179,129)
 assert (folder/'ALPINE.ID').read_text()=='asus-alpine-stock-kernel-v1\n'
 private=folder/'private';assert stat.S_ISDIR(private.lstat().st_mode)
 boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip();uuid.UUID(boot_id)
 backup=private/('bcb-before-stock-return-'+boot_id+'.bin')
 with backup.open('xb') as f:f.write(before);f.flush();os.fsync(f.fileno())
 assert backup.read_bytes()==before
 with para.open('r+b',buffering=0) as f:
  assert f.write(bytes(32))==32
  os.fsync(f.fileno())
 os.sync()
 with para.open('rb') as f:after=f.read(2048)
 assert after==stock and after[32:]==before[32:],'BCB read-back differs'
 changed=True
else:after=before
print(json.dumps({'next_ordinary_boot':'stock Android' if after==stock else 'Alpine recovery capsule','command_bytes_cleared':changed,'recovery_arguments':'empty','stock_boot_sha256_verified':True,'recovery_image_replaced':False}),flush=True)
if a.reboot:
 os.sync();subprocess.run(['/sbin/reboot'],check=True)
