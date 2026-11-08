from pathlib import Path
import subprocess as s,json,hashlib,re
R=Path('/srv/android/asus-network-runtime');P='/srv/android/asus-android17/kernel-bpf-fd';V='/srv/android/asus-virtual-validation/kernel-fd';pr='717bb3c9e13ce573cfdd2dda856debd27a0fa17f';vr='fcb1b6c2de6348e2724981dcd520dec631ed5255'
paths=['kernel/bpf','net','include/linux/bpf.h','include/linux/filter.h','include/linux/bpf-cgroup.h','include/uapi/linux/bpf.h','include/uapi/linux/filter.h','include/uapi/linux/if_tun.h','drivers/net/tun.c','drivers/net/veth.c','drivers/net/dummy.c','security/security.c','security/selinux/hooks.c','arch/arm64/net']
def tree(repo,rev):
 text=s.check_output(['git','-C',repo,'ls-tree','-r',rev,'--']+paths,text=True)
 return {l.split('\t')[1]:l.split()[2] for l in text.splitlines()}
p=tree(P,pr);v=tree(V,vr);assert p==v
files={}
for f,oid in p.items():
 data=(R/'kernel'/f).read_bytes();actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();files[f]=dict(baseline_git_object=oid,current_git_object=actual,current_sha256=hashlib.sha256(data).hexdigest(),unchanged=actual==oid)
report=dict(physical_commit=pr,virtual_commit=vr,baseline_equal=True,file_count=len(files),files=files)
(R/'evidence/network-source-equivalence.json').write_text(json.dumps(report,indent=2)+'\n')
def cfg(p):
 d={}
 for l in p.read_text().splitlines():
  m=re.match(r'(CONFIG_\w+)=(.*)',l)
  if m:d[m[1]]=m[2]
  m=re.match(r'# (CONFIG_\w+) is not set',l)
  if m:d[m[1]]='n'
 return d
p=cfg(R/'inputs/physical.config');v=cfg(R/'build-r1/.config');requested=json.loads((R/'evidence/network-config-requested.json').read_text());requested.update({k:p.get(k) for k in ['CONFIG_FILE_LOCKING','CONFIG_BLK_CGROUP','CONFIG_NAMESPACES','CONFIG_NET_NS']});diff={k:dict(physical=p.get(k),virtual=v.get(k)) for k in requested if p.get(k)!=v.get(k)}
core=['CONFIG_BPF','CONFIG_BPF_SYSCALL','CONFIG_CGROUP_BPF','CONFIG_BPF_JIT','CONFIG_HAVE_EBPF_JIT','CONFIG_BPF_JIT_ALWAYS_ON','CONFIG_BPF_UNPRIV_DEFAULT_OFF','CONFIG_NET_CLS_BPF','CONFIG_NET_CLS_MATCHALL','CONFIG_NET_ACT_BPF','CONFIG_NETFILTER_XT_MATCH_BPF','CONFIG_ANDROID_PARANOID_NETWORK','CONFIG_INET','CONFIG_IPV6','CONFIG_TUN','CONFIG_FILE_LOCKING']
report=dict(compared=len(requested),differences=diff,core={k:dict(physical=p.get(k),virtual=v.get(k),equal=p.get(k)==v.get(k)) for k in core},test_only_options=['CONFIG_DUMMY','CONFIG_VETH','CONFIG_NAMESPACES','CONFIG_NET_NS'],integration_requirement_from_firstboot={'CONFIG_BLK_CGROUP':'y','network_fixture_current':v.get('CONFIG_BLK_CGROUP'),'firstboot_image_sha256':'12c7ce00abe2a4a3adeadf87cda09a30479d61379f2b5bebf5534e1cd9238c27','cgroups_json_sha256':'ab2ed667ff45958843fb0c6ee953a5512def0ae87470c4358aa9576a6a4b2e22','status':'separate qualification supplied by firstboot owner; not changed by this spike'},physical_config_sha256=hashlib.sha256((R/'inputs/physical.config').read_bytes()).hexdigest(),virtual_config_sha256=hashlib.sha256((R/'build-r1/.config').read_bytes()).hexdigest())
(R/'evidence/network-config-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print('source files',len(files),'changed',[f for f in files if not files[f]['unchanged']]);print(json.dumps(report,indent=2))
