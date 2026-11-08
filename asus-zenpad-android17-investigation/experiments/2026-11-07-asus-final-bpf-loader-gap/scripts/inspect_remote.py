from pathlib import Path
import hashlib, json, subprocess as s, stat
O=Path('/srv/android/asus-final-bpf-loader-gap-20261107')
O.mkdir(exist_ok=False)
(O/'evidence').mkdir()
(O/'inputs').mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths={
 'selected_image': '/srv/android/asus-genuine-service-runtime/inputs/kernel-r7/Image',
 'selected_config': '/srv/android/asus-genuine-service-runtime/inputs/kernel-r7/config',
 'fixture_source': '/srv/android/asus-firstboot-runtime/kernel-cpuset-r1',
 'fixture_build': '/srv/android/asus-firstboot-runtime/kernel-build-r7',
 'physical_source': '/srv/android/asus-bmc156-full-kernel-r1/kernel',
 'physical_build': '/srv/android/asus-bmc156-full-kernel-r1/out',
 'qualified': '/srv/android/asus-network-runtime/handoff-r1',
}
result={'paths':paths,'files':{},'symbols':{}}
rels=['kernel/bpf/syscall.c','include/uapi/linux/bpf.h','kernel/bpf/Makefile','kernel/bpf/lpm_trie.c','net/core/filter.c']
for label in ['fixture_source','physical_source','qualified']:
 root=Path(paths[label]);root=root/'source' if label=='qualified' else root
 for rel in rels:
  p=root/rel;k=label+'/'+rel
  if not p.exists():result['files'][k]={'exists':False};continue
  t=p.read_text();result['files'][k]={'sha256':sha(p),'bytes':p.stat().st_size,'map_info_present':'BPF_OBJ_GET_INFO_BY_FD' in t,'helper68_present':'skb_load_bytes_relative' in t}
  if rel in rels[:2]:
   (O/'evidence'/(label+'-'+p.name)).write_text(t)
for label in ['fixture_build','physical_build']:
 root=Path(paths[label])
 for rel in ['.config','arch/arm64/boot/Image']:
  p=root/rel
  if p.exists():
   result['files'][label+'/'+rel]={'sha256':sha(p),'bytes':p.stat().st_size}
   if rel=='.config':
    result['files'][label+'/'+rel]['bpf_config']=[x for x in p.read_text().splitlines() if any(v in x for v in ['BPF','CGROUP','FILE_LOCKING','IKCONFIG'])]
 for rel in ['System.map','kernel/bpf/syscall.o']:
  p=root/rel
  if p.exists():
   if rel=='System.map':lines=p.read_text().splitlines()
   else:lines=s.check_output(['aarch64-linux-gnu-nm',str(p)],text=True).splitlines()
   result['symbols'][label+'/'+rel]=[x for x in lines if any(v in x for v in ['bpf_obj_get_info','bpf_map_get_info','SyS_bpf','sys_bpf','map_create'])]
for label in ['selected_image','selected_config']:
 p=Path(paths[label]);result['files'][label]={'exists':p.exists(),'resolved':str(p.resolve())}
 if p.is_file():result['files'][label].update(sha256=sha(p),bytes=p.stat().st_size)
root=Path('/srv/android/asus-genuine-service-runtime/inputs/kernel-r7')
result['selected_dir']=[p.name for p in root.iterdir()]
raw=Path('/srv/android/asus-radio-trigger-build-r4/system-partition.raw')
st=raw.stat();result['raw_identity']={'path':str(raw),'bytes':st.st_size,'inode':st.st_ino,'mtime_ns':st.st_mtime_ns,'mode':oct(stat.S_IMODE(st.st_mode))}
assert st.st_size==3753902080 and st.st_ino==28131263 and stat.S_IMODE(st.st_mode)==0o444
report=Path('/srv/android/asus-radio-trigger-build-r4/final-report.json')
assert sha(report)=='dd9d8d68ef77a35e188a894193b390d47cf6c10b56b8306909681a5672f80dba'
result['published_raw_sha256']=json.loads(report.read_text())['deliverables']['system']['sha256']
r=s.run(['/usr/sbin/debugfs','-R','ls -l /system/apex',str(raw)],capture_output=True,text=True,check=True,timeout=10)
result['apex_listing']=[x for x in r.stdout.splitlines() if 'tethering' in x]
print(json.dumps(result,indent=2))
(O/'evidence/inspection.json').write_text(json.dumps(result,indent=2))
