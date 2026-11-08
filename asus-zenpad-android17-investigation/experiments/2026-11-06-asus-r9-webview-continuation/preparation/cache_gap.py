import remote,json
from pathlib import Path
s=r'''
from pathlib import Path
import json,sys
R=Path('/srv/android/asus-reviewed-build-kit/r8');A=Path('/srv/android/lineage24');sys.path.insert(0,str(R/'scripts'))
from verify_product_r3 import log_entries
from compiler_channel import commands_for
r={};targets=set()
for phase,p in [('current',A/'out/.ninja_log'),('first',R/'attempt/native-evidence/host_init_verifier/.ninja_log'),('full',R/'attempt/native-evidence/bootimage/.ninja_log')]:
 rows=[]
 with p.open() as f:
  for l in f:
   fields=l.rstrip('\n').split('\t')
   if len(fields)==5 and any(n in fields[3] for n in ['system/bpf/loader/bpfloader/','system/vold/vold/','system/vold/libvold/']):rows.append(dict(output=fields[3],entry=fields[:3]+fields[4:]))
 r[phase]=rows;targets.update(x['output'] for x in rows)
cmds,receipts=commands_for(R,targets)
r['completed_without_current_requirement']={t:len(c) for t,c in cmds.items()};r['current_joined']=list(commands_for(R,targets,log_entries(A/'out/.ninja_log',targets))[0]);r['actual_gap']='Current .ninja_log may rotate per invocation; first-phase-only targets must not be silently accepted without a same-entry current join. No transitive dependency hashes were captured at execution.'
with Path('/srv/android/asus-reviewed-build-kit/r9/evidence/cache-gap.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/cache-gap.json').write_text(r);print(r[:7000])
