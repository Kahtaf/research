from pathlib import Path
import json,gzip,hashlib,struct,subprocess as s,re
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');sha=lambda b:hashlib.sha256(b).hexdigest();d={}
for run in ['run-trace','run-candidate','run-candidate-r2']:
 b=gzip.decompress((R/run/'initramfs.cpio.gz').read_bytes());pos=0;files={}
 while True:
  h=b[pos:pos+110];f=[int(h[6+i*8:14+i*8],16) for i in range(13)];n=b[pos+110:pos+110+f[11]-1].decode();pos=(pos+110+f[11]+3)//4*4;v=b[pos:pos+f[6]];pos=(pos+f[6]+3)//4*4
  if n=='TRAILER!!!':break
  if n!='entropy.seed':files[n]=sha(v)
 d[run]=dict(inputs={n:v for n,v in files.items() if n in ['init','system/bin/bpfloader','system/lib64/libbpf_android.so','system/vendor/etc/bpf/filterPowerSupplyEvents.o']},public_boundary_lines=[l for l in (R/run/'serial.log').read_text().splitlines() if any(x in l for x in ['CAPTURE','REPLAY','PACKET','ATTACH','TRACE_FIXTURE'])])
(R/'evidence/focused-replay.json').write_text(json.dumps(d,indent=2))
# Native ABI and dependencies used by the leaf; no active output mutation.
tool='/srv/android/lineage24/prebuilts/clang/host/linux-x86/clang-r584948b/bin/llvm-readelf';abi={}
for n in ['libbpf_android.so','libbpf_android.candidate.so']:
 out=s.run([tool,'--dyn-syms','-d',str(R/'inputs'/n)],capture_output=True,text=True,check=True).stdout
 abi[n]=dict(sha256=sha((R/'inputs'/n).read_bytes()),needed=re.findall(r'Shared library: \[([^]]+)\]',out),exports=[l.strip().split()[-1] for l in out.splitlines() if ' GLOBAL ' in l and ' UND ' not in l and ' FUNC ' in l])
assert abi['libbpf_android.so']['needed']==abi['libbpf_android.candidate.so']['needed'];assert abi['libbpf_android.so']['exports']==abi['libbpf_android.candidate.so']['exports'];(R/'evidence/leaf-abi.json').write_text(json.dumps(abi,indent=2))
p=R/'inputs/Loader.d';parts=p.read_text().replace('\\\n',' ').split(':',1)[1].split();A=Path('/srv/android/lineage24');deps={str(x):sha((A/x).read_bytes()) for x in parts if (A/x).is_file()};(R/'evidence/leaf-dependencies.json').write_text(json.dumps(deps,indent=2));print('dependency_files',len(deps));print('focused_receipts_written',list(d));print('abi_exports',abi['libbpf_android.candidate.so']['exports'])
