exec(open('2026-11-06-asus-r8-continuation-kit/preparation/inspect_remote.py').read().split('script=r')[0])
r=m.run(r'''
from pathlib import Path
import gzip,re,json,shlex,sys
R=Path('/srv/android/asus-reviewed-build-kit/r8');sys.path.insert(0,str(R/'scripts'))
from integrate import sha,read,write
from verify_product_r3 import BINARIES
P=R/'evidence/r7-native/verbose.log.gz'
assert sha(P)=='ac3b3a99e80ab47feef181073397fbc83837d6edcd035b30041913b5b01a77ee'
selected=read(R/'inputs/bpf-qualified-selection.json') if (R/'inputs/bpf-qualified-selection.json').exists() else read(read(R/'inputs/plan.json')['bpf_qualified_selection'])
mandatory_sources={s for module,ss in BINARIES.values() for s in ss};modules=[x[0] for x in BINARIES.values()]+['system/vold/libvold/']
bpf_outputs={t for row in selected['objects'] for t in row['graph_output_chain'] if t.startswith('out/soong/.intermediates/')}
finished=[];debug=[];total=0;failed=[]
for n,l in enumerate(gzip.open(P,'rt'),1):
 if re.match(r'^\[\d+/\d+\] ',l):
  total+=1
  if any(s in l for s in mandatory_sources|bpf_outputs) or any(s in l for s in modules):finished.append(dict(line=n,text=l.rstrip()))
 if l.startswith('FAILED: '):failed.append(dict(line=n,text=l.rstrip()))
 if l.startswith('verbose: ninja: ') and any(s in l for s in mandatory_sources):debug.append(dict(line=n,text=l.rstrip()))
# Pending debug commands are not successful execution and may name outputs that
# have not been built. Keep a small source-specific slice for review only.
result=dict(authentic_r7_verbose_sha256=sha(P),completed_action_lines=total,selected_completed_lines=finished,mandatory_pending_debug_examples=debug[:6],failed=failed,prior_r7_execution_accepted=[],policy='All fresh-required compiler/linker/BPF outputs must execute genuinely in r8; no timestamp relaxation or fixture substitution')
write(R/'inputs/r7-execution-disposition.json',result);print(json.dumps(result,indent=2))
''');Path('2026-11-06-asus-r8-continuation-kit/evidence/r7-command-disposition.json').write_text(r);d=json.loads(r);Path('2026-11-06-asus-r8-continuation-kit/inputs/r7-execution-disposition.json').write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in d.items() if k!='mandatory_pending_debug_examples'},indent=2))
