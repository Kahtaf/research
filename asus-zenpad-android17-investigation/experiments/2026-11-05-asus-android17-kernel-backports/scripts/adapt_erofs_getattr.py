#!/usr/bin/env python3
"""Retain the MT8163 tree's real statx-aware VFS API, without function casts."""
from pathlib import Path
import subprocess

source=Path('/srv/android/asus-android17/kernel')
def git(*args):
    return subprocess.check_output(['git',*args],cwd=source)
assert git('log','-1','--format=%s').decode().strip()=='fs: erofs: Adapt to the 4.9 block and VFS APIs'
assert b'const struct path *, struct kstat *, u32' in (source/'include/linux/fs.h').read_bytes()
# The preceding import has the same four-argument API that MT8163 already uses.
(source/'fs/erofs/inode.c').write_bytes(git('show','HEAD^:fs/erofs/inode.c'))
p=source/'fs/erofs/internal.h';s=p.read_text()
old='int erofs_getattr(struct vfsmount *mnt, struct dentry *dentry,\n\t\t  struct kstat *stat);'
new='int erofs_getattr(const struct path *path, struct kstat *stat,\n\t\t  u32 request_mask, unsigned int query_flags);'
assert s.count(old)==1;s=s.replace(old,new);p.write_text(s)
subprocess.run(['git','add','fs/erofs/inode.c','fs/erofs/internal.h'],cwd=source,check=True)
subprocess.run(['git','commit','-m','erofs: retain MT8163 statx-aware getattr API',
    '-m','The MT8163 4.9 baseline already uses the four-argument VFS getattr API. Restore the imported implementation/prototype while retaining the separate 4.9 bio and wakeup compatibility fixes.'],cwd=source,check=True)
patch=Path('/srv/android/asus-android17/patches/0009-mt8163-erofs-getattr.patch')
patch.write_bytes(git('format-patch','-1','--stdout'))
