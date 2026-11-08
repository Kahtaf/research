from pathlib import Path
import subprocess as s,os,resource,hashlib,json,gzip,stat,time,struct
O=Path('/srv/android/asus-final-bpf-loader-gap-20261107');R=O/'replay';R.mkdir(exist_ok=False)
os.environ['TMPDIR']=str(R)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=O/'replay_init.c'
cmd=['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra',str(source),'-o',str(R/'init')]
p=s.run(cmd,capture_output=True,text=True,timeout=20)
(R/'compile.json').write_text(json.dumps({'argv':cmd,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2));assert p.returncode==0,p.stderr
archive=bytearray()
def entry(name,mode,data=b'',major=0,minor=0):
 n=name.encode()+b'\0';fields=[1,mode,0,0,1,0,len(data),0,0,major,minor,len(n),0]
 archive.extend(b'070701'+''.join(f'{v:08x}' for v in fields).encode()+n);archive.extend(b'\0'*(-len(archive)%4));archive.extend(data);archive.extend(b'\0'*(-len(archive)%4))
entry('dev',stat.S_IFDIR|0o755);entry('dev/console',stat.S_IFCHR|0o600,major=5,minor=1)
entry('init',stat.S_IFREG|0o755,(R/'init').read_bytes());entry('TRAILER!!!',0)
initrd=R/'initramfs.cpio.gz';initrd.write_bytes(gzip.compress(archive,mtime=0))
kernel=Path('/srv/android/asus-genuine-service-runtime/inputs/kernel-r7/Image')
assert sha(kernel)=='95a62a8bccd3085d682a89b6c74c7afd0961cebd1e3137b256229849920b549b'
cmd=['qemu-system-aarch64','-machine','virt,gic-version=3','-accel','tcg,thread=single,tb-size=16','-cpu','cortex-a53','-smp','1','-m','384','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel',str(kernel),'-initrd',str(initrd),'-append','console=ttyAMA0 rdinit=/init panic=-1 loglevel=3']
receipt={'argv':cmd,'timeout_seconds':90,'kernel_sha256':sha(kernel),'init_sha256':sha(R/'init'),'initrd_sha256':sha(initrd),'source_sha256':sha(source),'purpose':'One minimal syscall replay, selected failed kernel; no Android init, disks, entropy input, properties, or BPF loader changes'}
(R/'command.json').write_text(json.dumps(receipt,indent=2));start=time.monotonic()
with (R/'serial.log').open('w') as log:
 p=s.run(cmd,stdin=s.DEVNULL,stdout=log,stderr=s.STDOUT,timeout=90)
text=(R/'serial.log').read_text();receipt={'qemu_exit':p.returncode,'elapsed_seconds':time.monotonic()-start,'timeout':False,'expected_missing_info_reproduced':'REPLAY_DONE expected_missing_info_reproduced=1' in text,'public_lines':[x for x in text.splitlines() if x.startswith(('ARRAY_','MAP_INFO','REPLAY_DONE'))]}
(R/'result.json').write_text(json.dumps(receipt,indent=2));assert receipt['expected_missing_info_reproduced'];print(json.dumps(receipt,indent=2))
