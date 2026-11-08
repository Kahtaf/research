from pathlib import Path
import re,json,subprocess as s,hashlib
O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106');T=Path('/srv/android/lineage24');B=O/'build/postimage'
trace=(B/'file-access.strace').read_text();bad=[]
for l in trace.splitlines():
 if '/srv/android/lineage24/out/' in l or '/srv/android/asus-network-runtime/' in l:bad.append(l)
# Relative out/ paths are inside snapshot cwd; no compiler chdir into the active source root is allowed.
chdir=[l for l in trace.splitlines() if 'chdir(' in l];assert not bad,bad[:10];assert not any('lineage24' in l for l in chdir),chdir
changed=[]
for p,v in json.loads((O/'evidence/toolchain-pins.json').read_text()).items():
 with (T/p).open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 if h!=v['sha256']:changed.append(p)
assert not changed,changed
out={'active_out_accesses':bad,'chdir_calls':chdir,'toolchain_hashes_unchanged':True,'trace_sha256':hashlib.sha256(trace.encode()).hexdigest(),'trace_bytes':len(trace)}
(O/'evidence/build-access-audit.json').write_text(json.dumps(out,indent=2)+'\n')
for name,path in [('postimage',O/'artifacts/bpfloader-postimage'),('prior-postimage',O/'inputs/prior/artifacts/bpfloader-legacy'),('preimage',O/'inputs/prior/inputs/platform-bpfloader')]:
 result=s.run(['aarch64-linux-gnu-readelf','-h','-l','-d','-n',str(path)],capture_output=True,text=True);(O/'evidence'/(name+'-elf.txt')).write_text(result.stdout+result.stderr)
print(json.dumps(out))
