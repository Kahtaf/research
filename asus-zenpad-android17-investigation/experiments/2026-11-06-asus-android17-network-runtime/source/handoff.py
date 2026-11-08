from pathlib import Path
import subprocess as s,hashlib,json,re,shutil,sys
R=Path('/srv/android/asus-network-runtime');O=R/('handoff-'+sys.argv[1]);O.mkdir();K=R/'kernel';repo='/srv/android/asus-android17/kernel-bpf-fd';rev='717bb3c9e13ce573cfdd2dda856debd27a0fa17f';P=O/'patches';P.mkdir();A=O/'apply-check';A.mkdir();F=O/'source';F.mkdir();E=O/'evidence';E.mkdir()
patches=['01-map-info.patch','02-lpm-trie.patch','03-skb-relative-load.patch','04-relative-net-without-mac.patch'];changed=['include/uapi/linux/bpf.h','kernel/bpf/syscall.c','kernel/bpf/Makefile','kernel/bpf/lpm_trie.c','net/core/filter.c'];files={}
for name in changed:
 base=s.run(['git','-C',repo,'show',rev+':'+name],capture_output=True);before=base.stdout if base.returncode==0 else None
 if before is not None:
  dest=A/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(before)
 files[name]={'baseline_sha256':hashlib.sha256(before).hexdigest() if before is not None else None,'tested_sha256':hashlib.sha256((K/name).read_bytes()).hexdigest()}
 dest=F/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(K/name,dest)
logs=[]
for name in patches:
 shutil.copyfile(R/'patches'/name,P/name)
 proc=s.run(['patch','--batch','--fuzz=0','-p1','-i',str(P/name)],cwd=A,capture_output=True,text=True);logs.append(dict(patch=name,exit=proc.returncode,stdout=proc.stdout,stderr=proc.stderr));assert proc.returncode==0,logs[-1]
for name in changed:assert (A/name).read_bytes()==(K/name).read_bytes(),name
(E/'physical-apply-validation.json').write_text(json.dumps(logs,indent=2)+'\n')
name='11-network-policy-and-required-loader.patch';shutil.copyfile(R/'patches'/name,P/name)
U=O/'connectivity-apply-check';U.mkdir();ufiles=['bpf/loader/NetBpfLoad.cpp','bpf/netd/BpfHandler.cpp','bpf/progs/netd.c'];um={}
for name in ufiles:
 before=(R/'inputs/Connectivity'/name).read_bytes();after=(R/'staged-network'/name).read_bytes();d=U/name;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(before);d=O/'connectivity-source'/name;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(after);um[name]=dict(baseline_sha256=hashlib.sha256(before).hexdigest(),tested_sha256=hashlib.sha256(after).hexdigest())
p=s.run(['patch','--batch','--fuzz=0','-p1','-i',str(P/'11-network-policy-and-required-loader.patch')],cwd=U,capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr
for name in ufiles:assert (U/name).read_bytes()==(R/'staged-network'/name).read_bytes()
(E/'connectivity-apply-validation.json').write_text(json.dumps(dict(exit=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2)+'\n')
for name in ['network-source-equivalence.json','network-config-equivalence.json','required-consumer-inventory.json','netd-object-source-match.json','relative-egress-fix.json','connectivity-head.txt','map-info-stage.json','lpm-stage.json']:
 shutil.copyfile(R/'evidence'/name,E/name)
for name,src in {'network.config':R/'build-r1/.config','physical-baseline.config':R/'inputs/physical.config','Image':R/'artifacts/network-qualified.Image','netd.o':R/'artifacts/bpf-network/netd.o','netbpfload':R/'artifacts/network_loader'}.items():shutil.copyfile(src,O/name)
for run in ['r5','r8','r9','r10','r13','r14']:
 dest=E/('run-'+run);dest.mkdir()
 for name in ['serial.log','result.json','inputs.json','qemu-command.json']:
  p=R/('run-'+run)/name
  if p.is_file():shutil.copyfile(p,dest/name)
log=(R/'run-r14/serial.log').read_text();counts={key:len(re.findall(pattern,log)) for key,pattern in {'map_metadata':r'^MAP_INFO .*ok=1','map_crud':r'^MAP_CRUD .*ok=1 restored=1','loopback_policy_packets':r'^POLICY_PACKET .*passed=1','routed_policy_packets':r'^NETWORK_PACKET .*passed=1','xtbpf_rule_operations':r'^XTBPF_RULE .*passed=1'}.items()}
# Anchored line checks, independent from the guest-complete marker.
counts={key:len(re.findall(pattern,log,re.M)) for key,pattern in {'map_metadata':r'^MAP_INFO .*ok=1','map_crud':r'^MAP_CRUD .*ok=1 restored=1','loopback_policy_packets':r'^POLICY_PACKET .*passed=1','routed_policy_packets':r'^NETWORK_PACKET .*passed=1','xtbpf_rule_operations':r'^XTBPF_RULE .*passed=1'}.items()}
assert 'KERNEL_API_RESULT checks=60 failures=0' in log and 'NETWORK_PATH_RESULT failures=0' in log and 'POLICY_RESULT failures=0' in log
assert counts['routed_policy_packets']==60 and counts['loopback_policy_packets']==10
manifest=dict(status='Qualified for reviewed integration as a targeted networking repair, not full Android/WiFi/Google readiness',physical_baseline_commit=rev,virtual_source_baseline='fcb1b6c2de6348e2724981dcd520dec631ed5255',kernel_patch_order=patches,connectivity_patch_order=['11-network-policy-and-required-loader.patch'],kernel_changed_files=files,connectivity_changed_files=um,tests=counts,api_checks=60,privilege_negative_checks=1,kernel_config_integration='No new physical config needed for this BPF series. Preserve physical FILE_LOCKING=y. Integrate separately qualified CONFIG_BLK_CGROUP=y from firstboot owner. Never copy the virtual config to hardware.',test_only_options=['CONFIG_DUMMY=y','CONFIG_VETH=y','CONFIG_NAMESPACES=y','CONFIG_NET_NS=y'],boundaries=['Real Linux 4.9 ARM64 QEMU; no external NIC/network exposure','Actual SDK37 ELF helpers and BpfHandler source harness, current genuine/rebuilt BPF objects','No Android Java VM/ConnectivityManager/DnsResolver integration or actual WiFi','Cross-profile loopback enforcement and SDK37 socket-create/UID permission migration not qualified; not to be silently marked ready','Remaining whole-platform-loader work is separate from this frozen qualified handoff'],sha256={str(p.relative_to(O)):hashlib.sha256(p.read_bytes()).hexdigest() for p in O.rglob('*') if p.is_file()})
(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(dict(path=str(O),tests=counts,image=manifest['sha256']['Image']),indent=2))
