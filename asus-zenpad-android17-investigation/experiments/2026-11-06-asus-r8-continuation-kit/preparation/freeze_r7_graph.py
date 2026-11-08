exec(open('2026-11-06-asus-r8-continuation-kit/preparation/inspect_remote.py').read().split('script=r')[0])
script=r'''
from pathlib import Path
import sys,json,hashlib,gzip,shutil,os,resource
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
R=Path('/srv/android/asus-reviewed-build-kit/r7');F=Path('/srv/android/asus-reviewed-build-kit/r8-fixtures/r7-evidence');F.mkdir(parents=True)
sys.path.insert(0,str(R/'scripts'))
from integrate import read,sha,write
from verify_product_r3 import BINARIES,selected_graph,log_entries
plan=read(R/'inputs/plan.json');A=Path(plan['aosp']);selected=read(plan['bpf_qualified_selection']);bpfs={t for row in selected['objects'] for t in row['graph_output_chain'] if t.startswith('out/soong/.intermediates/')}
required=set(BINARIES)|{x['install_path'] for x in selected['objects'] if x['install_path'].startswith('system/')}
graph,provenance=selected_graph(A,required,bpfs);write(F/'selected-graph.json',provenance)
targets=set(graph)|bpfs;entries=log_entries(A/'out/.ninja_log',targets)
metrics=[json.loads(l) for l in (A/'out/siso_metrics.json').open() if json.loads(l).get('output') in targets]
completed=[];pending=[]
for n,line in enumerate(gzip.open(A/'out/verbose.log.gz','rt',errors='replace'),1):
 if not any(tool in line for tool in ['clang','rustc','ld.lld']):continue
 hits=[t for t in targets if t in line]
 if hits:
  row=dict(line=n,text=line.rstrip(),targets=hits)
  (completed if line.startswith('[') else pending).append(row)
write(F/'selected-ninja-entries.json',entries);write(F/'selected-metrics.json',metrics);write(F/'finished-command-slices.json',completed)
for name in ['verbose.log.gz','.ninja_log','siso_metrics.json','siso_metadata.json','siso_localexec','siso_output','siso_failed_commands.sh']:
 shutil.copyfile(A/'out'/name,F/name)
write(F/'freeze-pins.json',{p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(F.iterdir()) if p.is_file()})
print(json.dumps(dict(graph_file_sha256=provenance['graph_sha256'],selected_graph_sha256=sha(F/'selected-graph.json'),selected_edges=len(graph),selected_ninja_entries=entries,selected_metrics=metrics,actual_finished_compiler_commands=completed,pending_debug_command_count=len(pending),frozen_pins=read(F/'freeze-pins.json'),policy_tools=[str(p) for base in ['/srv/android/asus-firstboot-runtime/inputs','/srv/android/asus-sdk37-lmkd-functional/inputs'] for p in Path(base).glob('**/checkfc') if p.is_file()][:10],policy_inputs=[str(p) for p in Path('/srv/android/asus-sdk37-lmkd-functional/inputs/fixture-r20/root').glob('**/*sepolicy*') if p.is_file()]),indent=2))
'''
r=m.run(script);Path('2026-11-06-asus-r8-continuation-kit/evidence/r7-execution-audit.json').write_text(r);d=json.loads(r);print(json.dumps({k:v for k,v in d.items() if k not in ['frozen_pins','graph_file_sha256','actual_finished_compiler_commands']},indent=2))
