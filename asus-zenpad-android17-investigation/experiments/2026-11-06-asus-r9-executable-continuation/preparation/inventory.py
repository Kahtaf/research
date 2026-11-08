import remote,json
from pathlib import Path
s=r'''
from pathlib import Path
import json,os,resource,signal,hashlib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(180,180));signal.alarm(240)
R=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1');F=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1-fixtures');R.mkdir();F.mkdir();(R/'inputs').mkdir();(R/'scripts').mkdir();(R/'evidence').mkdir()
O=Path('/srv/android/asus-reviewed-build-kit/r8');B=Path('/srv/android/asus-reviewed-build-kit/r9');plan=json.loads((O/'inputs/plan.json').read_text());sel=json.loads(Path(plan['bpf_qualified_selection']).read_text())
outputs={t for x in sel['objects'] for t in x['graph_output_chain'] if t.startswith('out/soong/')}
rows={}
for phase in ['host_init_verifier','bootimage']:
 metrics=[]
 for l in (O/'attempt/native-evidence'/phase/'siso_metrics.json').read_text().splitlines():
  m=json.loads(l)
  if m.get('output') in outputs:metrics.append({k:m.get(k) for k in ['output','step_id','cmdhash','err','error','rule','is_local']})
 rows[phase]=metrics
r=dict(bpf_selection=sel,bpf_native_rows=rows,external_sources={k:v for k,v in plan['external_pins'].items() if any(x in k for x in ['Sensors.cpp','service.cpp','sensors.c','accel_protocol'])},frozen36=list(json.loads((B/'evidence/selected-siso-state-v2.json').read_text())['selected_entries']),fixture_budget_bytes=805306368,limits=dict(cpu=1,address_space=1024**3,cpu_seconds=180,wall_seconds=240))
with (R/'evidence/inventory.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-executable-continuation/evidence/inventory.json').write_text(r);d=json.loads(r);print('BPF rows', {k:len(v) for k,v in d['bpf_native_rows'].items()});print('BPF targets',len({t for x in d['bpf_selection']['objects'] for t in x['graph_output_chain'] if t.startswith('out/soong/')}));print('frozen36',len(d['frozen36']));print('sources',d['external_sources'])
