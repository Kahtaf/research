from pathlib import Path
import subprocess as s,stat,gzip,json,hashlib,shutil,sys,os,re,resource,time
P=Path('/srv/android/asus-firstboot-runtime');R=Path('/srv/android/asus-sdk37-lmkd-functional');I=R/'inputs/fixture-r2';T=P/'inputs/boot-r10';E=P/'inputs/early-r1';name=sys.argv[1];assert re.fullmatch('r[0-9]+',name);O=R/('run-boot-'+name);O.mkdir()
shutil.copyfile(P/'source/seed_exec.c',O/'seed_exec.c')
os.environ['TMPDIR']=str(R/'tmp');(R/'tmp').mkdir(exist_ok=True)
commands=[]
def limits():
 os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(90,90))
def run(cmd):
 p=s.run(cmd,capture_output=True,text=True,preexec_fn=limits);commands.append(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));(O/'prepare-commands.json').write_text(json.dumps(commands,indent=2));assert p.returncode==0,(cmd,p.stdout,p.stderr);return p
run(['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra','-Werror',str(O/'seed_exec.c'),'-o',str(O/'seed-exec')])
for n,size in [('system',96*1024*1024)]:
 f=O/(n+'.ext4');f.touch();os.truncate(f,size)
 run(['mke2fs','-F','-t','ext4','-b','4096','-I','256','-O','none,has_journal,ext_attr,resize_inode,dir_index,filetype,extent,sparse_super,large_file,uninit_bg,dir_nlink,extra_isize','-E','lazy_itable_init=0,lazy_journal_init=0',str(f)])
run([str(T/'tools/e2fsdroid'),'-e','-T','1793984400','-S',str(T/'work/file_contexts.bin'),'-f',str(I/'root'),'-a','/',str(O/'system.ext4')])
files={'init':(O/'seed-exec').read_bytes(),'first-stage-init':(E/'init_first_stage').read_bytes(),'fstab.mt8163':(I/'fstab.mt8163').read_bytes(),'entropy.seed':os.urandom(64)}
a=bytearray()
def entry(name,mode,data=b'',major=0,minor=0):
 n=name.encode()+b'\0';v=[1,mode,0,0,1,0,len(data),0,0,major,minor,len(n),0];a.extend(b'070701'+''.join(f'{x:08x}' for x in v).encode()+n);a.extend(b'\0'*(-len(a)%4));a.extend(data);a.extend(b'\0'*(-len(a)%4))
for d in ['dev','proc','sys','system','first_stage_ramdisk','mnt','debug_ramdisk','second_stage_resources']:entry(d,stat.S_IFDIR|0o755)
entry('dev/console',stat.S_IFCHR|0o600,major=5,minor=1)
for n,b in files.items():entry(n,stat.S_IFREG|(0o755 if n in ['init','first-stage-init'] else 0o400 if n=='entropy.seed' else 0o644),b)
entry('TRAILER!!!',0);(O/'initramfs.cpio.gz').write_bytes(gzip.compress(a,mtime=0));(O/'cpio-manifest.json').write_text(json.dumps({n:hashlib.sha256(b).hexdigest() for n,b in files.items() if n!='entropy.seed'},indent=2))
cmd=['qemu-system-aarch64','-machine','virt,gic-version=3','-cpu','cortex-a53','-smp','1','-m','1996','-accel','tcg,thread=single,tb-size=64','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel',str(P/'kernel-build-r7/arch/arm64/boot/Image'),'-initrd',str(O/'initramfs.cpio.gz')]
for n in ['system']:cmd+=['-drive',f'file={O}/{n}.ext4,format=raw,if=none,id={n}','-device',f'virtio-blk-device,drive={n}']
cmd+=['-append','console=ttyAMA0 earlycon=pl011,0x9000000 rdinit=/init panic=-1 loglevel=7 printk.time=1 audit=1 printk.devkmsg=on androidboot.hardware=mt8163 androidboot.fstab_suffix=mt8163 androidboot.selinux=enforcing']
(O/'command.json').write_text(json.dumps(cmd,indent=2));code=None;timed=False
def qlimits():
 os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(3*1024**3,3*1024**3));resource.setrlimit(resource.RLIMIT_CPU,(90,90))
with (O/'serial.log').open('w') as f:
 try:code=s.run(cmd,stdin=s.DEVNULL,stdout=f,stderr=s.STDOUT,timeout=120,preexec_fn=qlimits).returncode
 except s.TimeoutExpired:timed=True
(O/'status.json').write_text(json.dumps(dict(returncode=code,timeout=timed),indent=2));print((O/'serial.log').read_text()[-18000:])

