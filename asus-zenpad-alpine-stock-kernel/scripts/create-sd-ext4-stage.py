#!/usr/bin/env python3
"""Create only the owned SD root image and verify its old-kernel mount."""
from pathlib import Path
import json,os,re,stat,subprocess,time
STATE=Path('/mnt/alpine-sd/2026-11-08-asus-alpine')
IMAGE=STATE/'alpine-root.ext4.partial'
TARGET=Path('/mnt/asus-root-stage')
RUN=Path('/run/asus-alpine')
FEATURES={'has_journal','extent','huge_file','flex_bg','uninit_bg','dir_nlink','extra_isize','sparse_super','large_file','filetype','resize_inode','dir_index','ext_attr'}
def phase(name,**fields):
 d={'phase':name,**fields};(RUN/'sd-root-build.json').write_text(json.dumps(d)+'\n');print(json.dumps(d),flush=True)
def run(*cmd,**kwargs):return subprocess.run(cmd,check=True,**kwargs)
assert (STATE/'ALPINE.ID').read_text()=='asus-alpine-stock-kernel-v1\n'
assert (STATE/'PERSISTENCE.ENABLE').read_text()=='asus-alpine-state-v1\n'
assert STATE.stat().st_dev==os.makedev(179,129)
assert os.statvfs(STATE).f_bavail*os.statvfs(STATE).f_frsize>1200*1024*1024
assert not IMAGE.exists() and not (STATE/'alpine-root.ext4').exists()
assert not TARGET.exists() or TARGET.is_dir() and not TARGET.is_symlink()
assert not os.path.ismount(TARGET)
(RUN/'sd-root-build.pid').write_text(str(os.getpid())+'\n')
phase('ALLOCATING_OWNED_1GIB_FILE')
with IMAGE.open('xb') as f:f.truncate(1073741824);f.flush();os.fsync(f.fileno())
phase('FORMATTING_OWNED_FILE')
run('mke2fs','-q','-F','-t','ext4','-b','4096','-I','256','-N','32768','-m','0','-L','asus-alpine','-O','none,'+','.join(sorted(FEATURES)),'-E','lazy_itable_init=0,lazy_journal_init=0',str(IMAGE))
header=subprocess.check_output(['dumpe2fs','-h',str(IMAGE)],text=True,stderr=subprocess.DEVNULL)
actual=set(re.search(r'^Filesystem features:\s*(.*)$',header,re.M)[1].split())
assert actual==FEATURES,(actual,FEATURES)
phase('FEATURE_ALLOWLIST_MATCH',features=sorted(actual))
loop=subprocess.check_output(['losetup','-f'],text=True).strip()
assert re.fullmatch('/dev/loop[0-9]+',loop)
major,minor=map(int,Path('/sys/class/block',Path(loop).name,'dev').read_text().split(':'))
s=Path(loop).stat();assert stat.S_ISBLK(s.st_mode) and s.st_rdev==os.makedev(major,minor)
run('losetup',loop,str(IMAGE));TARGET.mkdir(mode=0o700,exist_ok=True)
run('mount','-t','ext4','-o','rw,noatime',loop,str(TARGET))
assert TARGET.stat().st_dev==s.st_rdev
proof=TARGET/'.stock-kernel-mount-proof';proof.write_text('stock Linux3.18.35 ext4 read-write pass\n')
with proof.open('rb') as f:os.fsync(f.fileno())
os.sync();assert proof.read_text()=='stock Linux3.18.35 ext4 read-write pass\n'
phase('EXT4_MOUNT_RW_PASS_READY_TO_POPULATE',loop=loop,image=str(IMAGE),target=str(TARGET),features=sorted(actual))
