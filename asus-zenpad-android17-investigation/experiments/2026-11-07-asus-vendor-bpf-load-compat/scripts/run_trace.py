from pathlib import Path
import os,subprocess as s,gzip,stat,json,hashlib,struct,time
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');K=Path('/srv/android/asus-android-runtime-network-parity-20261107/build/arch/arm64/boot/Image');assert hashlib.sha256(K.read_bytes()).hexdigest()=='aaa35347bd751c3e79eac78608f1a37d5a5cc1c34429773c257b91bb17e4bf47'
x=s.run(['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra',str(R/'source/trace_init.c'),'-o',str(R/'inputs/trace-init')],capture_output=True,text=True);(R/'evidence/trace-compile.json').write_text(json.dumps(dict(rc=x.returncode,stderr=x.stderr),indent=2));assert x.returncode==0,x.stderr
base=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106/inputs/runtime-root-r2');files={str(p.relative_to(base)):p.read_bytes() for p in base.rglob('*') if p.is_file() and ('/lib64/' in str(p) or p.name in ['linker64','property_info'])}
C=Path('/srv/android/asus-final-bpf-runtime-20261106/capture/root');files.update({str(p.relative_to(C)):p.read_bytes() for p in C.rglob('*') if p.is_file() and '/lib64/' in str(p)})
raw=Path('/srv/android/asus-radio-trigger-build-r4/system-partition.raw')
for n in ['system/bin/bpfloader','system/lib64/libbpf_android.so']:
 p=s.run(['debugfs','-R','cat /'+n,str(raw)],capture_output=True,check=True);assert p.stdout[:4]==b'\x7fELF';files[n]=p.stdout;(R/'inputs'/Path(n).name).write_bytes(p.stdout)
files['system/vendor/etc/bpf/filterPowerSupplyEvents.o']=(R/'inputs/installed-filter.o').read_bytes();files['init']=(R/'inputs/trace-init').read_bytes();files['entropy.seed']=os.urandom(64)
(R/'inputs/trace-files.json').write_text(json.dumps({n:hashlib.sha256(b).hexdigest() for n,b in files.items() if n!='entropy.seed'},indent=2))
archive=bytearray()
def entry(n,mode,b=b'',major=0,minor=0):
 nb=n.encode()+b'\0';vals=[1,mode,0,0,1,0,len(b),0,0,major,minor,len(nb),0];archive.extend(b'070701'+''.join(f'{v:08x}' for v in vals).encode()+nb);archive.extend(b'\0'*(-len(archive)%4));archive.extend(b);archive.extend(b'\0'*(-len(archive)%4))
dirs={'dev','proc','sys','tmp','data','linkerconfig'}
for n in files:dirs.update(str(p) for p in Path(n).parents if str(p)!='.')
for d in sorted(dirs,key=lambda x:(x.count('/'),x)):entry(d,stat.S_IFDIR|0o755)
entry('vendor',stat.S_IFLNK|0o777,b'/system/vendor');entry('dev/console',stat.S_IFCHR|0o600,major=5,minor=1)
for n,b in files.items():entry(n,stat.S_IFREG|0o755,b)
entry('TRAILER!!!',0);O=R/'run-trace';O.mkdir();(O/'initramfs.cpio.gz').write_bytes(gzip.compress(archive,mtime=0));os.chmod(O/'initramfs.cpio.gz',0o400)
cmd=['qemu-system-aarch64','-machine','virt,gic-version=3','-accel','tcg,thread=single,tb-size=16','-cpu','cortex-a53','-smp','1','-m','384','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel',str(K),'-initrd',str(O/'initramfs.cpio.gz'),'-append','console=ttyAMA0 rdinit=/init panic=-1 loglevel=4 printk.devkmsg=on'];(O/'command.json').write_text(json.dumps(cmd,indent=2));start=time.monotonic()
with (O/'serial.log').open('w') as f:
 try:p=s.run(cmd,stdin=s.DEVNULL,stdout=f,stderr=s.STDOUT,timeout=60);rc=p.returncode;timeout=False
 except s.TimeoutExpired:rc=None;timeout=True
text=(O/'serial.log').read_text(errors='replace');(O/'result.json').write_text(json.dumps(dict(rc=rc,timeout=timeout,elapsed=time.monotonic()-start,completed='TRACE_FIXTURE_DONE' in text),indent=2));print(text[-16000:])
