from pathlib import Path
import subprocess as s,stat,gzip,json,hashlib,os,resource,time,datetime
R=Path('/srv/android/asus-sdk37-lmkd-functional'); O=R/'run-kernel-negative-r1';O.mkdir()
def limits():
 os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
cmd=['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra','-Werror',str(R/'source/kernel_probe.c'),'-o',str(O/'probe')]
p=s.run(cmd,capture_output=True,text=True,preexec_fn=limits);(O/'compile.json').write_text(json.dumps(dict(argv=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0,p.stderr
a=bytearray()
def entry(n,mode,b=b'',maj=0,min=0):
 name=n.encode()+b'\0';v=[1,mode,0,0,1,0,len(b),0,0,maj,min,len(name),0];a.extend(b'070701'+''.join(f'{x:08x}' for x in v).encode()+name);a.extend(b'\0'*(-len(a)%4));a.extend(b);a.extend(b'\0'*(-len(a)%4))
for d in ['dev','proc','sys']:entry(d,stat.S_IFDIR|0o755)
entry('dev/console',stat.S_IFCHR|0o600,maj=5,min=1);entry('init',stat.S_IFREG|0o755,(O/'probe').read_bytes());entry('TRAILER!!!',0);(O/'initramfs.gz').write_bytes(gzip.compress(a,mtime=0))
K=Path('/srv/android/asus-firstboot-runtime/kernel-build-r7/arch/arm64/boot/Image')
cmd=['qemu-system-aarch64','-machine','virt,gic-version=3','-cpu','cortex-a53','-smp','1','-m','2048','-accel','tcg,thread=single,tb-size=64','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel',str(K),'-initrd',str(O/'initramfs.gz'),'-append','console=ttyAMA0 rdinit=/init panic=-1 loglevel=6']
(O/'command.json').write_text(json.dumps(cmd,indent=2));(O/'input-hashes.json').write_text(json.dumps({str(f):{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in [K,R/'source/kernel_probe.c',O/'probe',O/'initramfs.gz']},indent=2))
def qlimits():
 os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(3*1024**3,3*1024**3));resource.setrlimit(resource.RLIMIT_CPU,(90,90))
t=time.monotonic();code=None;timed=False
with (O/'serial.log').open('w') as f:
 p=s.Popen(cmd,stdin=s.DEVNULL,stdout=f,stderr=s.STDOUT,preexec_fn=qlimits);(O/'started.json').write_text(json.dumps(dict(pid=p.pid,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),wall_limit=120,cpu_limit=90,address_space_limit=3*1024**3)))
 try:code=p.wait(timeout=120)
 except s.TimeoutExpired:timed=True;p.kill();code=p.wait()
(O/'status.json').write_text(json.dumps(dict(returncode=code,timeout=timed,seconds=time.monotonic()-t),indent=2));print((O/'serial.log').read_text()[-7000:])
