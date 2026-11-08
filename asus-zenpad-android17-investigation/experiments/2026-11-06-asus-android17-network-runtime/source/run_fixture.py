from pathlib import Path
import subprocess as s,json,hashlib,os,stat,gzip,sys,shutil
R=Path('/srv/android/asus-network-runtime');I=R/'inputs';O=R/('run-'+sys.argv[1]);O.mkdir();os.environ['TMPDIR']=str(O)
for n in ['guest_init.c','loader_probe.cpp','run_fixture.py']:shutil.copyfile(R/'source'/n,O/n)
cmd=['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra',str(R/'source/guest_init.c'),'-o',str(O/'init')]
reuse=os.environ.get('NETWORK_REUSE_INIT')
if reuse:
 shutil.copyfile(reuse,O/'init');shutil.copyfile(Path(reuse).parent/'guest_init.c',O/'guest_init.c');(O/'compile.log').write_text('Reused existing compiled fixture init: '+reuse+'\n')
else:
 p=s.run(cmd,capture_output=True,text=True);(O/'compile.log').write_text(json.dumps(cmd)+'\n'+p.stdout+p.stderr);assert p.returncode==0,p.stderr
files={str(p.relative_to(I/'root')):p.read_bytes() for p in (I/'root').rglob('*') if p.is_file()}
mode=sys.argv[3] if len(sys.argv)>3 else 'original'
for p in (R/'artifacts/bpf-original').glob('*.o'):
 if '.unstripped.' not in p.name:files['apex/com.android.tethering/etc/bpf/mainline/'+p.name]=p.read_bytes()
if mode in ('core','network'):files['apex/com.android.tethering/etc/bpf/mainline/netd.o']=(R/('artifacts/bpf-'+mode+'/netd.o')).read_bytes()
if os.environ.get('NETWORK_WHOLE'):
 for p in (I/'platform-root').rglob('*'):
  if p.is_file():files[str(p.relative_to(I/'platform-root'))]=p.read_bytes()
 if os.environ.get('NETWORK_PLATFORM_STAGED'):files['system/bin/bpfloader']=(R/'artifacts/bpfloader-legacy').read_bytes()
 files['whole-loader']=b'1'
 if os.environ.get('NETWORK_WHOLE_ONLY'):files['whole-loader-only']=b'1'
 files['system/bin/network_loader']=(R/'artifacts/network_loader').read_bytes()
 files['apex/com.android.tethering/bin/netbpfload']=(R/'artifacts/network_loader').read_bytes()
if os.environ.get('NETWORK_NEGATIVE_ONLY'):
 files['negative-only']=b'1'
 files['system/bin/loader_negative']=(R/'artifacts/loader_negative').read_bytes()
 files['system/bin/cross_profile_probe']=(R/'artifacts/cross_profile_probe').read_bytes()
files['system/bin/iptables']=(R/'artifacts/iptables').read_bytes()
files['system/bin/ip6tables']=(R/'artifacts/iptables').read_bytes()
files['system/bin/kernel_api_probe']=(R/'artifacts/kernel_api_probe').read_bytes()
files['init']=(O/'init').read_bytes();files['entropy.seed']=os.urandom(64)
for name in ['loader_probe','seed_properties','handler_probe','policy_probe','network_probe']:files['system/bin/'+name]=(R/'artifacts'/name).read_bytes()
archive=bytearray()
def entry(name,mode,data=b'',major=0,minor=0):
 n=name.encode()+b'\0';fields=[1,mode,0,0,1,0,len(data),0,0,major,minor,len(n),0];archive.extend(b'070701'+''.join(f'{v:08x}' for v in fields).encode()+n);archive.extend(b'\0'*(-len(archive)%4));archive.extend(data);archive.extend(b'\0'*(-len(archive)%4))
dirs={'dev','proc','sys','tmp','data','linkerconfig','mnt'}
for n in files:dirs.update(str(p) for p in Path(n).parents if str(p)!='.')
for d in sorted(dirs,key=lambda x:(x.count('/'),x)):entry(d,stat.S_IFDIR|0o755)
entry('dev/console',stat.S_IFCHR|0o600,major=5,minor=1)
for n,b in sorted(files.items()):entry(n,stat.S_IFREG|(0o755 if n=='init' or '/bin/' in n else 0o644),b)
entry('TRAILER!!!',0);(O/'initramfs.cpio.gz').write_bytes(gzip.compress(archive,mtime=0))
k=Path(sys.argv[2]) if len(sys.argv)>2 else I/'baseline.Image'
cmd=['qemu-system-aarch64','-machine','virt,gic-version=3','-cpu','cortex-a53','-smp','1','-m','1536','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel',str(k),'-initrd',str(O/'initramfs.cpio.gz'),'-append','console=ttyAMA0 rdinit=/init panic=-1 loglevel=6 printk.devkmsg=on']
(O/'qemu-command.json').write_text(json.dumps(cmd,indent=2)+'\n');(O/'inputs.json').write_text(json.dumps({n:hashlib.sha256(b).hexdigest() for n,b in files.items() if n!='entropy.seed'},indent=2))
code=None;timeout=False
with (O/'serial.log').open('w') as f:
 try:code=s.run(cmd,stdin=s.DEVNULL,stdout=f,stderr=s.STDOUT,timeout=180).returncode
 except s.TimeoutExpired:timeout=True
log=(O/'serial.log').read_text(errors='replace');result=dict(qemu_exit=code,timeout=timeout,complete='NETWORK_DONE' in log,kernel_sha256=hashlib.sha256(k.read_bytes()).hexdigest(),boundary='whole NetBpfLoad/platform loader in minimal fixture; no Android service boot' if os.environ.get('NETWORK_WHOLE') else 'targeted real loader helpers; no Android service boot')
(O/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));print('\n'.join(log.splitlines()[-100:]))
