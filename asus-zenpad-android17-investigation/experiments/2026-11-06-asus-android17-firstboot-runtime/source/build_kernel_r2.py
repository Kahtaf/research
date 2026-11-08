from pathlib import Path
import subprocess as s,shutil,re,json,os,hashlib
R=Path('/srv/android/asus-firstboot-runtime');P=Path('/srv/android/asus-android17-runtime-prereqs');K=R/'kernel';B=R/'kernel-build-r2';assert K.exists() and not B.exists();B.mkdir();(R/'tmp').mkdir(exist_ok=True);os.environ['TMPDIR']=str(R/'tmp')
shutil.copyfile(R/'inputs/early-r1/kernel.config',B/'.config');shutil.copyfile(P/'inputs/physical.config',R/'inputs/physical-baseline.config')
def parse(p):
 d={}
 for l in p.read_text().splitlines():
  m=re.match(r'(CONFIG_\w+)=(.*)',l)
  if m:d[m[1]]=m[2]
  m=re.match(r'# (CONFIG_\w+) is not set',l)
  if m:d[m[1]]='n'
 return d
physical=parse(R/'inputs/physical-baseline.config');prior=parse(B/'.config');prefix=('CONFIG_CGROUP','CONFIG_MEMCG','CONFIG_NAMESPACES','CONFIG_UTS_NS','CONFIG_IPC_NS','CONFIG_PID_NS','CONFIG_NET_NS','CONFIG_USER_NS','CONFIG_SECCOMP','CONFIG_SECURITY','CONFIG_AUDIT','CONFIG_KEYS','CONFIG_UNIX','CONFIG_FHANDLE','CONFIG_TMPFS','CONFIG_INOTIFY','CONFIG_FANOTIFY','CONFIG_EPOLL','CONFIG_SIGNALFD','CONFIG_TIMERFD','CONFIG_EVENTFD','CONFIG_TASKSTATS','CONFIG_TASK_DELAY','CONFIG_TASK_XACCT','CONFIG_TASK_IO','CONFIG_BLK_CGROUP','CONFIG_FAIR_GROUP_SCHED','CONFIG_CFS_BANDWIDTH','CONFIG_RT_GROUP_SCHED','CONFIG_COMPAT','CONFIG_PERF_EVENTS')
selected={k:v for k,v in physical.items() if k.startswith(prefix)}
for k,v in selected.items():
 if prior.get(k,'n')==v:continue
 args=['-e' if v=='y' else '-d' if v=='n' else '-m',k[7:]] if v in ['y','n','m'] else ['--set-str' if v.startswith('"') else '--set-val',k[7:],v.strip('"')]
 s.run([str(K/'scripts/config'),'--file',str(B/'.config')]+args,check=True)
args=['make','-C',str(K),'O='+str(B),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','KBUILD_BUILD_USER=asus-port','KBUILD_BUILD_HOST=firstboot-runtime','KBUILD_BUILD_VERSION=1','KBUILD_BUILD_TIMESTAMP=Fri Nov 6 00:00:00 UTC 2026']
s.run(args+['olddefconfig'],check=True)
actual=parse(B/'.config');comparison=[dict(option=k,physical=v,virtual=actual.get(k,'n'),matches=v==actual.get(k,'n')) for k,v in selected.items()];(R/'evidence/core-kconfig-comparison.json').write_text(json.dumps(comparison,indent=2));assert all(c['matches'] for c in comparison),[c for c in comparison if not c['matches']]
p=s.run([str(K/'scripts/diffconfig'),str(R/'inputs/early-r1/kernel.config'),str(B/'.config')],capture_output=True,text=True);(R/'evidence/kernel-config-delta.txt').write_text(p.stdout)
(R/'evidence/kernel-command.json').write_text(json.dumps(args+['-j1','Image'],indent=2));p=s.run(args+['-j1','Image']);(R/'evidence/kernel-status.json').write_text(json.dumps(dict(returncode=p.returncode)));assert p.returncode==0
(R/'evidence/kernel-hashes.json').write_text(json.dumps({str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [B/'.config',B/'arch/arm64/boot/Image']},indent=2))
