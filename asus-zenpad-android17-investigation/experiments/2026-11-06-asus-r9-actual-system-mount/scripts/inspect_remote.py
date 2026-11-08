import os,pathlib,json,stat,hashlib,resource,signal
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(90);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
P=pathlib.Path
R=P('/srv/android/asus-r9-actual-system-mount-20261106');assert not R.exists();R.mkdir()
raw=P('/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw')
fd=os.open(raw,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC);s=os.fstat(fd)
assert stat.S_ISREG(s.st_mode) and s.st_size==3753902080 and stat.S_IMODE(s.st_mode)==0o444
identity=lambda s:dict(dev=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,mode=oct(stat.S_IMODE(s.st_mode)))
I=P('/srv/android/asus-full-system-observer-preparation-20261106/immutable')
pins=json.loads((I.parent/'immutable-pins.json').read_text())
selected={r['relative']:r['sha256']for r in pins if r['relative']in ['Image','sources/.config','sources/ext4.h','sources/super.c','bin/qemu-system-aarch64','bin/aarch64-linux-gnu-gcc']}
d=dict(raw=str(raw),before=identity(s),parent_supplied_sha256='baa69560ace09a478c902077d8ff926d7a079ecb9b9f1632e4c330169b243798',immutable_root=str(I),selected_pins=selected,superblock_hex=os.pread(fd,1024,1024).hex(),raw_open_flags='O_RDONLY|O_NOFOLLOW|O_CLOEXEC')
os.close(fd)
(R/'inspection.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
