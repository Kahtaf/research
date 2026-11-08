from pathlib import Path
import os,json,subprocess as s,resource,datetime,stat,sys
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');I=R/'inputs/runtime-r2';E=R/'evidence';phase=sys.argv[1] if len(sys.argv)>1 else 'patch';assert phase in ['patch','runtime'];O=R/('run-'+phase+'-r2');O.mkdir();os.environ['TMPDIR']=str(R/'tmp');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});admit=json.loads((E/'root-enabled-admission.json').read_text());raw=Path(admit['raw_identity']['path'])
def identity():
 x=raw.stat();return dict(path=str(raw),dev=x.st_dev,inode=x.st_ino,bytes=x.st_size,mtime_ns=x.st_mtime_ns,ctime_ns=x.st_ctime_ns,mode=oct(stat.S_IMODE(x.st_mode)))
assert identity()==admit['raw_identity']
if phase=='runtime':assert json.loads((E/'runtime-r2-cow-verification.json').read_text())['passed'] and 'COW_PATCH_COMPLETE modified=3 added_bin_directory=1' in (R/'run-patch-r2/serial.log').read_text()
cmd=['/usr/bin/qemu-system-aarch64','-machine','virt,gic-version=3','-accel','tcg,tb-size=64,thread=single','-cpu','cortex-a53','-smp','1','-m','1024','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel','/srv/android/asus-genuine-service-runtime/inputs/kernel-r7/Image','-initrd',str(I/('patch-initramfs.cpio.gz' if phase=='patch' else 'runtime-initramfs.cpio.gz'))]
for spec in [dict(driver='file',filename=str(raw),**{'node-name':'basefile','read-only':True}),dict(driver='raw',file='basefile',**{'node-name':'base','read-only':True}),dict(driver='file',filename=str(I/'system.qcow2'),**{'node-name':'cowfile','read-only':phase=='runtime'}),dict(driver='qcow2',file='cowfile',backing='base',**{'node-name':'system','read-only':phase=='runtime'})]:cmd+=['-blockdev',json.dumps(spec,separators=(',',':'))]
cmd+=['-device','virtio-blk-device,drive=system']
if phase=='runtime':cmd+=['-drive',f'file={I}/data.ext4,format=raw,if=none,id=data','-device','virtio-blk-device,drive=data']
args='console=ttyAMA0 earlycon=pl011,0x9000000 rdinit=/init panic=-1 loglevel=7 printk.time=1 audit=1 printk.devkmsg=on'
if phase=='runtime':args+=' androidboot.hardware=mt8163 androidboot.fstab_suffix=mt8163 androidboot.selinux=enforcing'
cmd+=['-append',args];(O/'command.json').write_text(json.dumps(cmd,indent=2));seconds=45 if phase=='patch' else 90;status=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),wall_limit_seconds=seconds,raw_before=identity(),cpu_affinity=list(os.sched_getaffinity(0)),phase=phase)
def limit():
 resource.setrlimit(resource.RLIMIT_AS,(2560*1024**2,2560*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(seconds,seconds));resource.setrlimit(resource.RLIMIT_FSIZE,(768*1024**2,768*1024**2));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with (O/'serial.log').open('wb') as f:
 try:status.update(returncode=s.run(cmd,stdin=s.DEVNULL,stdout=f,stderr=s.STDOUT,timeout=seconds,preexec_fn=limit).returncode,timeout=False)
 except s.TimeoutExpired:status.update(returncode=None,timeout=True)
status.update(finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),raw_after=identity(),raw_identity_unchanged=identity()==admit['raw_identity'],owned_allocated_bytes=sum(p.stat().st_blocks*512 for p in R.rglob('*') if p.is_file() and not p.is_symlink()),owned_logical_bytes=sum(p.stat().st_size for p in R.rglob('*') if p.is_file() and not p.is_symlink()))
(O/'status.json').write_text(json.dumps(status,indent=2));assert status['raw_identity_unchanged'] and status['owned_logical_bytes']<(2*1024+256)*1024**2;print(json.dumps(status,indent=2));print((O/'serial.log').read_text()[-5000:])
