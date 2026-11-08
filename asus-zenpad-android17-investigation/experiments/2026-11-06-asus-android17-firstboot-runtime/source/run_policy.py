from pathlib import Path
import subprocess as s,stat,gzip,json,hashlib
R=Path('/srv/android/asus-firstboot-runtime');I=R/'inputs/early-r1';O=R/'run-policy-r2';O.mkdir()
cmd=['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra','-Werror',str(R/'source/policy_probe.c'),'-o',str(O/'init')]
p=s.run(cmd,capture_output=True,text=True);(O/'compile.json').write_text(json.dumps(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0,p.stderr
archive=bytearray()
def entry(name,mode,data=b'',major=0,minor=0):
 n=name.encode()+b'\0';v=[1,mode,0,0,1,0,len(data),0,0,major,minor,len(n),0];archive.extend(b'070701'+''.join(f'{x:08x}' for x in v).encode()+n);archive.extend(b'\0'*(-len(archive)%4));archive.extend(data);archive.extend(b'\0'*(-len(archive)%4))
for d in ['dev','proc','sys']:entry(d,stat.S_IFDIR|0o755)
entry('dev/console',stat.S_IFCHR|0o600,major=5,minor=1)
entry('init',stat.S_IFREG|0o755,(O/'init').read_bytes());entry('policy',stat.S_IFREG|0o644,(I/'root/policy').read_bytes());entry('TRAILER!!!',0)
(O/'initramfs.cpio.gz').write_bytes(gzip.compress(archive,mtime=0))
cmd=['qemu-system-aarch64','-machine','virt,gic-version=3','-cpu','cortex-a53','-smp','1','-m','1024','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel',str(I/'Image'),'-initrd',str(O/'initramfs.cpio.gz'),'-append','console=ttyAMA0 earlycon=pl011,0x9000000 rdinit=/init panic=-1 loglevel=7 enforcing=1']
(O/'command.json').write_text(json.dumps(cmd,indent=2));code=None;timeout=False
with (O/'serial.log').open('w') as f:
 try:code=s.run(cmd,stdin=s.DEVNULL,stdout=f,stderr=s.STDOUT,timeout=60).returncode
 except s.TimeoutExpired:timeout=True
(O/'status.json').write_text(json.dumps(dict(returncode=code,timeout=timeout),indent=2));print((O/'serial.log').read_text())
