from pathlib import Path
import os,resource,json,hashlib,subprocess as s,gzip,stat,time
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
O=Path('/srv/android/asus-linux49-power-supply-filter-20261106');K=Path('/srv/android/asus-network-runtime/handoff-r1/Image');cfg=K.parent/'network.config';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(K)=='f48955e15b0210d0b14c9d8036b6655e353a02c9e46ae5fc015b252b9bd8eac6';assert sha(cfg)=='8323724c579329c40f33aa15531320e2fdefc7e8d190703d56a555eac890ba01'
init=r'''#include <stdio.h>
#include <sys/mount.h>
#include <sys/resource.h>
#include <sys/reboot.h>
#include <sys/wait.h>
#include <unistd.h>
int main(void){setvbuf(stdout,0,_IONBF,0);puts("FILTER_FIXTURE_BEGIN");mount("proc","/proc","proc",0,0);mount("sysfs","/sys","sysfs",0,0);mount("devtmpfs","/dev","devtmpfs",0,0);struct rlimit l={RLIM_INFINITY,RLIM_INFINITY};setrlimit(RLIMIT_MEMLOCK,&l);pid_t p=fork();if(!p){execl("/test","/test","kernel",(char*)0);_exit(127);}int st;waitpid(p,&st,0);printf("FILTER_TEST_EXIT exited=%d exit=%d signal=%d\n",WIFEXITED(st),WIFEXITED(st)?WEXITSTATUS(st):-1,WIFSIGNALED(st)?WTERMSIG(st):0);puts("FILTER_FIXTURE_DONE");sync();reboot(RB_POWER_OFF);return 0;}
''';(O/'source/guest_init.c').write_text(init);cmd=['aarch64-linux-gnu-gcc','-static','-O2',str(O/'source/guest_init.c'),'-o',str(O/'artifacts/init')];p=s.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
R=O/'run-r7';R.mkdir();files={'init':(O/'artifacts/init').read_bytes(),'test':(O/'artifacts/test-guest').read_bytes(),'baseline-insns':(O/'artifacts/baseline-insns').read_bytes(),'candidate-insns':(O/'artifacts/candidate-insns').read_bytes()};archive=bytearray()
def entry(name,mode,data=b'',major=0,minor=0):
 n=name.encode()+b'\0';vals=[1,mode,0,0,1,0,len(data),0,0,major,minor,len(n),0];archive.extend(b'070701'+''.join(f'{v:08x}' for v in vals).encode()+n);archive.extend(b'\0'*(-len(archive)%4));archive.extend(data);archive.extend(b'\0'*(-len(archive)%4))
for d in ['dev','proc','sys']:entry(d,stat.S_IFDIR|0o755)
entry('dev/console',stat.S_IFCHR|0o600,major=5,minor=1)
for n,b in files.items():entry(n,stat.S_IFREG|0o755,b)
entry('TRAILER!!!',0);(R/'initramfs.cpio.gz').write_bytes(gzip.compress(archive,mtime=0));del archive
cmd=['qemu-system-aarch64','-machine','virt,gic-version=3','-accel','tcg,thread=single,tb-size=16','-cpu','cortex-a53','-smp','1','-m','384','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel',str(K),'-initrd',str(R/'initramfs.cpio.gz'),'-append','console=ttyAMA0 rdinit=/init panic=-1 loglevel=4'];(R/'command.json').write_text(json.dumps(dict(argv=cmd,timeout_seconds=90,rlimit_as_bytes=1024**3,cpu_affinity=list(os.sched_getaffinity(0)),kernel_sha256=sha(K),config_sha256=sha(cfg),input_sha256={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}),indent=2));start=time.monotonic()
with (R/'serial.log').open('w') as log:
 try:p=s.run(cmd,stdin=s.DEVNULL,stdout=log,stderr=s.STDOUT,timeout=90);code=p.returncode;timeout=False
 except s.TimeoutExpired:code=None;timeout=True
text=(R/'serial.log').read_text(errors='replace');result=dict(qemu_exit=code,timeout=timeout,complete='FILTER_FIXTURE_DONE' in text,elapsed_seconds=time.monotonic()-start,peak_child_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,serial_sha256=sha(R/'serial.log'),kernel_config_unchanged=sha(K)=='f48955e15b0210d0b14c9d8036b6655e353a02c9e46ae5fc015b252b9bd8eac6' and sha(cfg)=='8323724c579329c40f33aa15531320e2fdefc7e8d190703d56a555eac890ba01',owned_allocation_bytes=sum(p.stat().st_blocks*512 for p in O.rglob('*') if p.is_file()));(R/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));print(text[-12000:])
