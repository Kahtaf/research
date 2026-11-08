from pathlib import Path
import os,sys,json,hashlib,gzip,stat,subprocess as s,resource,time
O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
mode=sys.argv[1];assert mode in ('preimage','postimage','mandatory-negative');R=O/('run-'+mode+'-r2');R.mkdir(exist_ok=False)
files={str(p.relative_to(O/'inputs/runtime-root-r2')):p.read_bytes() for p in (O/'inputs/runtime-root-r2').rglob('*') if p.is_file()}
files['system/bin/bpfloader']=(O/('inputs/prior/inputs/platform-bpfloader' if mode=='preimage' else 'artifacts/bpfloader-postimage')).read_bytes()
if mode=='mandatory-negative':files['apex/com.android.tethering/etc/bpf/mainline/netd.o']=b'OWNED_NEGATIVE_NOT_AN_ELF\n'
files['init']=(O/'artifacts/fixture-init-r2').read_bytes();files['entropy.seed']=os.urandom(64)
archive=bytearray()
def entry(name,mode,data=b'',major=0,minor=0):
 n=name.encode()+b'\0';fields=[1,mode,0,0,1,0,len(data),0,0,major,minor,len(n),0];archive.extend(b'070701'+''.join(f'{v:08x}' for v in fields).encode()+n);archive.extend(b'\0'*(-len(archive)%4));archive.extend(data);archive.extend(b'\0'*(-len(archive)%4))
dirs={'dev','proc','sys','tmp','data','linkerconfig','mnt','system/vendor/etc/bpf'}
for n in files:dirs.update(str(p) for p in Path(n).parents if str(p)!='.')
for d in sorted(dirs,key=lambda x:(x.count('/'),x)):entry(d,stat.S_IFDIR|0o755)
entry('vendor',stat.S_IFLNK|0o777,b'/system/vendor');entry('dev/console',stat.S_IFCHR|0o600,major=5,minor=1)
for n,b in sorted(files.items()):entry(n,stat.S_IFREG|(0o755 if n=='init' or '/bin/' in n else 0o644),b)
entry('TRAILER!!!',0);(R/'initramfs.cpio.gz').write_bytes(gzip.compress(archive,mtime=0));del archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(R/'inputs.json').write_text(json.dumps({n:hashlib.sha256(b).hexdigest() for n,b in files.items()},indent=2)+'\n');del files
cmd=['qemu-system-aarch64','-machine','virt,gic-version=3','-accel','tcg,thread=single,tb-size=16','-cpu','cortex-a53','-smp','1','-m','384','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel',str(O/'inputs/network-qualified.Image'),'-initrd',str(R/'initramfs.cpio.gz'),'-append','console=ttyAMA0 rdinit=/init panic=-1 loglevel=6 printk.devkmsg=on']
(R/'command.json').write_text(json.dumps({'argv':cmd,'rlimit_as_bytes':1024**3,'cpu_affinity':list(os.sched_getaffinity(0)),'guest_ram_mib':384,'timeout_seconds':180,'started':time.time(),'kernel_sha256':sha(O/'inputs/network-qualified.Image'),'initramfs_sha256':sha(R/'initramfs.cpio.gz')},indent=2)+'\n')
with (R/'serial.log').open('w') as f:
 try:
  p=s.run(['/usr/bin/time','-v','-o',str(R/'host-resources.txt'),*cmd],stdin=s.DEVNULL,stdout=f,stderr=s.STDOUT,timeout=180);code=p.returncode;timeout=False
 except s.TimeoutExpired:code=None;timeout=True
text=(R/'serial.log').read_text(errors='replace');result={'qemu_exit':code,'timeout':timeout,'complete':'PLATFORM_FIXTURE_DONE' in text,'expected_stage':mode,'loader_exit_125':'EXEC_RESULT /system/bin/network_loader rc=125' in text,'mainline_done':'WHOLE_LOADER_RESULT mainline_done=1' in text,'kernel_sha256':sha(O/'inputs/network-qualified.Image'),'log_sha256':sha(R/'serial.log')}
(R/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
print('\n'.join(l for l in text.splitlines() if any(x in l for x in ['EXEC_RESULT','WHOLE_LOADER','ACTUAL_UNAME','Error when loading','below its kernel minimum','PLATFORM_FIXTURE_'])))
