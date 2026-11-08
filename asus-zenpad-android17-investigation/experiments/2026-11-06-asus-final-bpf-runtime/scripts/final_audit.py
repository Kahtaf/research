from pathlib import Path
import json,hashlib,stat,os,resource,time
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
O=Path('/srv/android/asus-final-bpf-runtime-20261106');c=json.loads((O/'evidence/capture.json').read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
p=Path(c['raw_before']['path']);st=p.stat();raw=dict(path=str(p),bytes=st.st_size,mode=oct(stat.S_IMODE(st.st_mode)),inode=st.st_ino,mtime_ns=st.st_mtime_ns,sha256=sha(p));assert raw==c['raw_before']
for r in c['objects']:assert sha(O/'capture/root'/r['install_path'])==r['current_sha256']
for r,v in c['loaders'].items():assert sha(O/'capture/root'/r)==v['sha256']
paths=['/srv/android/asus-network-runtime/handoff-r1/Image','/srv/android/asus-network-runtime/handoff-r1/network.config','/srv/android/asus-network-runtime/handoff-r1/manifest.json','/srv/android/asus-sdk37-platform-bpf-startup-20261106/supplement-qualified-r2/manifest.json']
d=json.loads(Path('/srv/android/asus-root-enabled-incremental-r1/host-r2/validation/r8-product-provenance.json').read_text());matches=[]
for r in d['payloads']:
 if 'bpfload' in str(r.get('path','')):matches.append(r)
a=dict(raw_after_runtime=raw,raw_unchanged=True,captured_objects_unchanged=True,captured_loaders_unchanged=True,original_remote_pins={p:sha(Path(p)) for p in paths},loader_completed_host_rows=matches,additional_loader=dict(path='apex/com.android.uprobestats/bin/uprobestatsbpfload',sha256=sha(O/'capture/com.android.uprobestats-selected-apex/bin/uprobestatsbpfload')),owned_allocation_bytes=sum(p.stat().st_blocks*512 for p in O.rglob('*') if p.is_file()),scope='No active source/output writes. Actual final captured loader/object execution, unchanged qualified fixture libraries. No property seed, property service or readiness setter. No QEMU timeouts occurred.')
assert a['owned_allocation_bytes']<=1024**3
(O/'evidence/final-audit.json').write_text(json.dumps(a,indent=2));print(json.dumps({k:v for k,v in a.items() if k!='loader_completed_host_rows'},indent=2))
