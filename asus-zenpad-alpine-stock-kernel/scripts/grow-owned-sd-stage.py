#!/usr/bin/env python3
"""Increase only the newly created SD image to the measured usable capacity."""
from pathlib import Path
import json,os,re,subprocess
run=Path('/run/asus-alpine');state=json.loads((run/'sd-root-build.json').read_text())
assert state['phase']=='EXT4_MOUNT_RW_PASS_READY_TO_POPULATE'
image=Path(state['image']);target=Path(state['target']);loop=state['loop']
assert str(image)=='/mnt/alpine-sd/2026-11-08-asus-alpine/alpine-root.ext4.partial'
assert image.stat().st_size==1073741824
assert sorted(p.name for p in target.iterdir())==['.stock-kernel-mount-proof','lost+found']
def phase(name):
 state['phase']=name;(run/'sd-root-build.json').write_text(json.dumps(state)+'\n');print(name,flush=True)
subprocess.run(['umount',str(target)],check=True);subprocess.run(['losetup','-d',loop],check=True)
phase('GROWING_OWNED_IMAGE_TO_2GIB')
with image.open('r+b') as f:f.truncate(2147483648);f.flush();os.fsync(f.fileno())
subprocess.run(['e2fsck','-f','-p',str(image)],check=True)
subprocess.run(['resize2fs',str(image)],check=True)
header=subprocess.check_output(['dumpe2fs','-h',str(image)],text=True,stderr=subprocess.DEVNULL)
actual=set(re.search(r'^Filesystem features:\s*(.*)$',header,re.M)[1].split());assert actual==set(state['features'])
subprocess.run(['losetup',loop,str(image)],check=True)
subprocess.run(['mount','-t','ext4','-o','rw,noatime',loop,str(target)],check=True)
assert (target/'.stock-kernel-mount-proof').read_text()=='stock Linux3.18.35 ext4 read-write pass\n'
state['image_bytes']=2147483648;phase('EXT4_2GIB_RW_PASS_READY_TO_POPULATE')
