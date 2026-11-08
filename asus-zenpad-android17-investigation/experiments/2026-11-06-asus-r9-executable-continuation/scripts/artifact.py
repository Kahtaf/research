"""Exact source-cohort artifact admission and parent-only atomic materialization."""
import hashlib
import os
from pathlib import Path
import shutil
import zipfile

REL='external/chromium-webview/prebuilt/arm64/webview.apk'
OID='1d2f61832b2596b0046cb82cf3634609ea866098d097a83fac27c35272ac726a'
SIZE=260835655
POINTER=b'version https://git-lfs.github.com/spec/v1\noid sha256:'+OID.encode()+b'\nsize 260835655\n'
BEFORE='a7b12c1895a3b354a91997fffe0e383a88e5b0e0d4371f8fdc090c71f62aade7'
COMMIT='5de662a4d42b57a2efe4114e499d38fa3ce41f9d'
ORIGIN='https://github.com/LineageOS/android_external_chromium-webview_prebuilt_arm64'

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def require(value,message):
    if not value:raise ValueError(message)

def admit(path,expected_sha=OID,expected_size=SIZE):
    p=Path(path)
    require(not p.is_symlink() and p.is_file(),'Artifact must be a regular file')
    require(p.stat().st_size==expected_size,'Artifact size mismatch')
    require(digest(p)==expected_sha,'Artifact SHA256 mismatch')
    with zipfile.ZipFile(p) as z:
        require(len(z.namelist())==len(set(z.namelist())),'Duplicate ZIP entry')
        require('AndroidManifest.xml' in z.namelist(),'Missing actual Android manifest')
        require(z.testzip() is None,'ZIP CRC failure')
    return dict(sha256=expected_sha,bytes=expected_size)

def check_preimage(path):
    p=Path(path)
    require(not p.is_symlink() and p.is_file() and p.read_bytes()==POINTER,'Exact source pointer preimage changed')

def materialize(src,dst,backup):
    """Only called inside the parent supervisor's continuous original flock."""
    dst=Path(dst);backup=Path(backup)
    check_preimage(dst);admit(src)
    require(not dst.parent.is_symlink(),'Symlink destination parent')
    backup.parent.mkdir(parents=True,exist_ok=True)
    with dst.open('rb') as inp,backup.open('xb') as out:
        shutil.copyfileobj(inp,out);out.flush();os.fsync(out.fileno())
    check_preimage(backup)
    saved_dir=os.open(backup.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(saved_dir)
    finally:os.close(saved_dir)
    tmp=dst.with_name(dst.name+'.reviewed-r9-tmp')
    with Path(src).open('rb') as inp,tmp.open('xb') as out:
        shutil.copyfileobj(inp,out,1048576);out.flush();os.fsync(out.fileno())
    admit(tmp);check_preimage(dst)
    os.replace(tmp,dst)
    fd=os.open(dst.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return admit(dst)
