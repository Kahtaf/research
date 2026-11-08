from pathlib import Path
import os,subprocess as s,json,resource,datetime,hashlib,stat,sys
R=Path('/srv/android/asus-r9-actual-early-runtime-20261106');I=R/'inputs';E=R/'evidence';G=Path('/srv/android/asus-genuine-service-runtime');phase=sys.argv[1] if len(sys.argv)>1 else 'patch';assert phase in ['patch','runtime']
os.environ['TMPDIR']=str(R/'tmp');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
raw=Path('/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw');pins=json.loads((E/'input-pins.json').read_text())
def ident():
 st=raw.stat();return dict(path=str(raw),dev=st.st_dev,inode=st.st_ino,bytes=st.st_size,mtime_ns=st.st_mtime_ns,ctime_ns=st.st_ctime_ns,mode=oct(stat.S_IMODE(st.st_mode)))
expected={k:v for k,v in pins['raw'].items() if k!='sha256_inherited'};assert ident()==expected
O=R/('run-'+phase+('-2' if phase=='patch' else '-1'));O.mkdir()
if phase=='runtime':
 assert 'COW_PATCH_COMPLETE files_changed=1 files_added=2' in (R/'run-patch-2/serial.log').read_text()
 assert json.loads((E/'cow-file-verification.json').read_text())['passed']
 data=I/'data.ext4';data.touch(exist_ok=False);os.truncate(data,512*1024**2)
 mk=['mke2fs','-F','-t','ext4','-b','4096','-I','256','-O','none,has_journal,ext_attr,resize_inode,dir_index,filetype,extent,sparse_super,large_file,uninit_bg,dir_nlink,extra_isize','-E','lazy_itable_init=0,lazy_journal_init=0',str(data)]
 p=s.run(mk,capture_output=True,text=True,timeout=60);(O/'data-format.json').write_text(json.dumps(dict(command=mk,rc=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0
cmd=['/usr/bin/qemu-system-aarch64','-machine','virt,gic-version=3','-accel','tcg,tb-size=64,thread=single','-cpu','cortex-a53','-smp','1','-m','1024','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel',str(G/'inputs/kernel-r7/Image'),'-initrd',str(I/('patch-initramfs.cpio.gz' if phase=='patch' else 'runtime-initramfs.cpio.gz'))]
for spec in [dict(driver='file',filename=str(raw),**{'node-name':'basefile','read-only':True}),dict(driver='raw',file='basefile',**{'node-name':'base','read-only':True}),dict(driver='file',filename=str(I/'system.qcow2'),**{'node-name':'cowfile','read-only':phase=='runtime'}),dict(driver='qcow2',file='cowfile',backing='base',**{'node-name':'system','read-only':phase=='runtime'})]:cmd+=['-blockdev',json.dumps(spec,separators=(',',':'))]
cmd+=['-device','virtio-blk-device,drive=system']
if phase=='runtime':cmd+=['-drive',f'file={I}/data.ext4,format=raw,if=none,id=data','-device','virtio-blk-device,drive=data']
args='console=ttyAMA0 earlycon=pl011,0x9000000 rdinit=/init panic=-1 loglevel=7 printk.time=1 audit=1 printk.devkmsg=on'
if phase=='runtime':args+=' androidboot.hardware=mt8163 androidboot.fstab_suffix=mt8163 androidboot.selinux=enforcing'
cmd+=['-append',args];(O/'command.json').write_text(json.dumps(cmd,indent=2));limit=45 if phase=='patch' else 90
status=dict(phase=phase,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),launcher_pid=os.getpid(),wall_limit_seconds=limit,cpu_affinity=list(os.sched_getaffinity(0)),qemu_sha256=hashlib.sha256(Path('/usr/bin/qemu-system-aarch64').read_bytes()).hexdigest(),raw_before=ident())
(O/'started.json').write_text(json.dumps(status,indent=2))
def limits():
 resource.setrlimit(resource.RLIMIT_AS,(2560*1024**2,2560*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(limit,limit));resource.setrlimit(resource.RLIMIT_FSIZE,(768*1024**2,768*1024**2))
with (O/'serial.log').open('w') as f:
 try:status.update(returncode=s.run(cmd,stdin=s.DEVNULL,stdout=f,stderr=s.STDOUT,timeout=limit,preexec_fn=limits).returncode,timeout=False)
 except s.TimeoutExpired:status.update(returncode=None,timeout=True)
status.update(finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),raw_after=ident(),raw_identity_unchanged=ident()==expected,owned_allocated_bytes=sum(p.lstat().st_blocks*512 for p in R.rglob('*') if p.is_file()),owned_logical_bytes=sum(p.lstat().st_size for p in R.rglob('*') if p.is_file()))
(O/'status.json').write_text(json.dumps(status,indent=2));assert status['raw_identity_unchanged'] and status['owned_allocated_bytes']<=2*1024**3 and status['owned_logical_bytes']<=2*1024**3
print(json.dumps(status,indent=2));print((O/'serial.log').read_text()[-14000:])
