from pathlib import Path
import os,json,subprocess as s,datetime,stat,sys,resource,time
R=Path('/srv/android/asus-final-image-startup-20261107');I=R/'inputs';E=R/'evidence';phase=sys.argv[1];assert phase in ['patch','runtime'];O=R/('run-'+phase);O.mkdir();os.environ['TMPDIR']=str(R/'tmp');cpus=sorted(os.sched_getaffinity(0));os.sched_setaffinity(0,set(cpus[:(2 if phase=='runtime' else 1)]));admit=json.loads((E/'admission.json').read_text());raw=Path(admit['system']['path'])
def identity(p):
 x=p.stat();return dict(path=str(p),dev=x.st_dev,inode=x.st_ino,bytes=x.st_size,mtime_ns=x.st_mtime_ns,ctime_ns=x.st_ctime_ns,mode=oct(stat.S_IMODE(x.st_mode)))
assert identity(raw)==admit['system'];assert identity(Path(admit['boot']['path']))==admit['boot']
if phase=='runtime':
 assert json.loads((E/'cow-verification.json').read_text())['passed']
 assert 'COW_PATCH_COMPLETE modified=2 added_observer=2' in (R/'run-patch/serial.log').read_text()
 assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime(2026,11,7,14,40,tzinfo=datetime.timezone.utc),'Too late for safe bounded run'
cmd=['/usr/bin/qemu-system-aarch64','-machine','virt,gic-version=3','-accel','tcg,tb-size=64,thread='+('multi' if phase=='runtime' else 'single'),'-cpu','cortex-a53','-smp','2' if phase=='runtime' else '1','-m','2048' if phase=='runtime' else '256','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel','/srv/android/asus-genuine-service-runtime/inputs/kernel-r7/Image','-initrd',str(I/('patch-initramfs.cpio.gz' if phase=='patch' else 'runtime-initramfs.cpio.gz'))]
for spec in [dict(driver='file',filename=str(raw),**{'node-name':'basefile','read-only':True}),dict(driver='raw',file='basefile',**{'node-name':'base','read-only':True}),dict(driver='file',filename=str(I/'system.qcow2'),**{'node-name':'cowfile','read-only':phase=='runtime'}),dict(driver='qcow2',file='cowfile',backing='base',**{'node-name':'system','read-only':phase=='runtime'})]:cmd+=['-blockdev',json.dumps(spec,separators=(',',':'))]
cmd+=['-device','virtio-blk-device,drive=system']
if phase=='runtime':cmd+=['-drive',f'file={I}/data.ext4,format=raw,if=none,id=data','-device','virtio-blk-device,drive=data']
args='console=ttyAMA0 earlycon=pl011,0x9000000 rdinit=/init panic=-1 loglevel=7 printk.time=1 audit=1 printk.devkmsg=on'
if phase=='runtime':args+=' androidboot.hardware=mt8163 androidboot.fstab_suffix=mt8163 androidboot.selinux=enforcing'
cmd+=['-append',args];(O/'command.json').write_text(json.dumps(cmd,indent=2));seconds=45 if phase=='patch' else 600
status=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),wall_limit_seconds=seconds,system_before=identity(raw),boot_before=identity(Path(admit['boot']['path'])),cpu_affinity=sorted(os.sched_getaffinity(0)),phase=phase,rlimit_as_added=False)
resource.setrlimit(resource.RLIMIT_CORE,(0,0));start=time.monotonic()
with (O/'serial.log').open('wb') as f:
 with s.Popen(cmd,stdin=s.DEVNULL,stdout=f,stderr=s.STDOUT) as p:
  status['owned_qemu_pid']=p.pid;(O/'started.json').write_text(json.dumps(status,indent=2))
  try:status.update(returncode=p.wait(timeout=seconds),timeout=False)
  except s.TimeoutExpired:
   p.kill();p.wait();status.update(returncode=p.returncode,timeout=True,termination='Owned subprocess PID killed at declared wall bound; no other process targeted')
status.update(finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_wall_seconds=time.monotonic()-start,system_after=identity(raw),boot_after=identity(Path(admit['boot']['path'])),base_identity_unchanged=identity(raw)==admit['system'],boot_identity_unchanged=identity(Path(admit['boot']['path']))==admit['boot'])
(O/'status.json').write_text(json.dumps(status,indent=2));assert status['base_identity_unchanged'] and status['boot_identity_unchanged'];print(json.dumps(status,indent=2));print((O/'serial.log').read_text()[-5000:])
