from pathlib import Path
import os,resource,json,hashlib,stat,base64,re
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
O=Path('/srv/android/asus-final-netd-runtime-20261106');F=Path('/srv/android/asus-final-bpf-runtime-20261106');N=Path('/srv/android/asus-network-runtime');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((O/'evidence/capture.json').read_text());raw=Path(c['raw_before']['path']);st=raw.stat();ident=dict(path=str(raw),bytes=st.st_size,mode=oct(stat.S_IMODE(st.st_mode)),inode=st.st_ino,mtime_ns=st.st_mtime_ns);assert all(ident[k]==c['raw_before'][k] for k in ident)
for p,h in json.loads((O/'evidence/frozen-receipts-sha256.json').read_text()).items():assert sha(Path(p))==h
for row in c['objects']:assert sha(F/'capture/root'/row['install_path'])==row['current_sha256']
for p,row in c['loaders'].items():assert sha(F/'capture/root'/p)==row['sha256']
assert sha(N/'handoff-r1/Image')=='f48955e15b0210d0b14c9d8036b6655e353a02c9e46ae5fc015b252b9bd8eac6'
assert sha(N/'handoff-r1/network.config')=='8323724c579329c40f33aa15531320e2fdefc7e8d190703d56a555eac890ba01'
runs={}
for R in sorted(O.glob('run-*')):
 if not (R/'result.json').exists():continue
 t=(R/'serial.log').read_text(errors='replace');runs[R.name]=dict(result=json.loads((R/'result.json').read_text()),exits=re.findall(r'EXEC_RESULT (\S+) rc=(\d+)',t),boundaries=[x for x in t.splitlines() if '_BOUNDARY' in x or 'CONNECTIVITY_MAINLINE_DONE' in x],counts={k:len(re.findall(k,t)) for k in ['MAP_INFO .*ok=1','MAP_CRUD .*ok=1 restored=1','POLICY_PACKET .*passed=1','NETWORK_PACKET .*passed=1','NETWORK_PACKET .*passed=0','OBJECT_RESULT .*ok=0']},last_results=[x for x in t.splitlines() if 'RESULT failures=' in x],resources=(R/'host-resources.txt').read_text())
allocation=sum(p.stat().st_blocks*512 for p in O.rglob('*') if p.is_file());assert allocation<=512*1024**2
out=dict(runs=runs,raw_stat_after=ident,raw_full_hash_not_repeated=True,frozen_receipts_unchanged=True,all26_captured_objects_unchanged=True,loaders_unchanged=True,allocation_bytes=allocation,kernel_sha256=sha(N/'handoff-r1/Image'),config_sha256=sha(N/'handoff-r1/network.config'),properties=json.loads((O/'evidence/property-seeds.json').read_text()))
(O/'evidence/final-audit-owned.json').write_text(json.dumps(out,indent=2))
files={}
for p in O.rglob('*'):
 if p.is_file() and (p.suffix in ['.json','.log','.txt','.c','.cpp','.py','.prop','.rc'] or p.name=='seed_properties.d') and p.stat().st_size<2000000:files[str(p.relative_to(O))]=base64.b64encode(p.read_bytes()).decode()
print(json.dumps(files))
