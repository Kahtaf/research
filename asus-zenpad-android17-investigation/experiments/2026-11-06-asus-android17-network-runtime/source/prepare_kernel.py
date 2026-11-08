from pathlib import Path
import subprocess as s,shutil,json,re
R=Path('/srv/android/asus-network-runtime');K=R/'kernel';K.mkdir()
repo='/srv/android/asus-virtual-validation/kernel-fd';v='fcb1b6c2de6348e2724981dcd520dec631ed5255'
a=s.Popen(['git','-C',repo,'archive',v],stdout=s.PIPE);s.run(['tar','xf','-','-C',str(K)],stdin=a.stdout,check=True);assert a.wait()==0
B=R/'build-r1';B.mkdir();shutil.copyfile(R/'inputs/baseline.config',B/'.config')
def cfg(p):
 d={}
 for l in p.read_text().splitlines():
  m=re.match(r'(CONFIG_\w+)=(.*)',l)
  if m:d[m[1]]=m[2]
  m=re.match(r'# (CONFIG_\w+) is not set',l)
  if m:d[m[1]]='n'
 return d
physical=cfg(R/'inputs/physical.config'); selected={k:v for k,v in physical.items() if re.match(r'CONFIG_(BPF|HAVE_EBPF|CGROUP_BPF|NETFILTER|NF_|NET_CLS|NET_ACT|NET_SCH|NET_INGRESS|IP_NF|IP6_NF|IPV6|INET|IP_ADVANCED|IP_MULTIPLE|IP_ROUTE|IP_MROUTE|NET_NS|NAMESPACES|CGROUPS|PACKET|UNIX|TUN|DUMMY|VETH|XFRM|BRIDGE_NETFILTER|NET$)',k)}
for k,v in selected.items():
 args=['-e' if v=='y' else '-d' if v=='n' else '-m' if v=='m' else '--set-val',k.removeprefix('CONFIG_')]
 if v not in ['y','n','m']:args.append(v)
 s.run([str(K/'scripts/config'),'--file',str(B/'.config')]+args,check=True)
for k in ['NET','INET','NETDEVICES','NET_SCHED','NET_CLS','NET_CLS_ACT','NETFILTER','NETFILTER_ADVANCED','NETFILTER_XTABLES','CGROUPS','CGROUP_BPF','TUN','VETH','DUMMY']:
 s.run([str(K/'scripts/config'),'--file',str(B/'.config'),'-e',k],check=True)
(R/'evidence/network-config-requested.json').write_text(json.dumps(selected,indent=2)+'\n')
