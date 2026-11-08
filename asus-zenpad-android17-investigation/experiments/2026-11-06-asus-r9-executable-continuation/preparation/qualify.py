from pathlib import Path
import base64,json,remote
R=Path(__file__).resolve().parents[1]
files={str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode() for folder in ['scripts','tests','inputs/root-property-path-fix'] for p in (R/folder).glob('*') if p.is_file()}
s='FILES='+repr(files)+'\n'+r'''
from pathlib import Path
import os,resource,signal,base64,json,sys,subprocess,time
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(240,240));resource.setrlimit(resource.RLIMIT_FSIZE,(512*1024**2,512*1024**2));signal.alarm(300)
R=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1');F=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1-fixtures')
for rel,b in FILES.items():
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(b))
sys.path.insert(0,str(R/'scripts'))
from cache_lineage import Session
from integrate import read,audit_inputs,sha
from graph_context import selected_graph
plan=read(R/'inputs/plan.json');started=time.monotonic();session=Session(R,plan)
lineage=session.preflight();graph,receipt=selected_graph(Path(plan['aosp']),session.catalog,session.rows)
from verify_product_r3 import BINARIES,chain
checks=[]
for relative,(module,sources) in BINARIES.items():
 target='out/target/product/p00a/'+relative;closure=chain(graph,target)
 linked=[t for t in closure if '/unstripped/' in t and Path(t).name==Path(relative).name and module in t]
 assert len(linked)==1,(relative,linked)
 assert linked[0] in session.rows,linked[0]
 for source in sources:
  candidates=[t for t in closure if source in graph[t]['inputs'] and t.startswith('out/soong/')]
  assert candidates and all(t in session.rows for t in candidates),(source,candidates)
  for target in candidates:session.record(target,source)
 checks.append(dict(relative=relative,link_output=linked[0],source_count=len(sources)))
audit=audit_inputs(plan,baseline=False)
with (F/'lineage-current-records.json').open('w') as f:json.dump(session.accepted,f,indent=2)
with (F/'selected-graph.json').open('w') as f:json.dump(receipt,f,indent=2)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
p=subprocess.run([sys.executable,'-B','-m','unittest','discover','-v','-s',str(R/'tests')],capture_output=True,text=True,env=env,timeout=120)
(F/'tests.stdout.log').write_text(p.stdout);(F/'tests.stderr.log').write_text(p.stderr)
r=dict(script_sha256={p.name:sha(p) for p in (R/'scripts').iterdir() if p.is_file()},lineage=lineage,source_audit=audit,selected_edges=len(graph),selected_binary_graph_checks=checks,tests_exit_code=p.returncode,tests_tail=p.stderr[-6000:],elapsed_seconds=time.monotonic()-started,active_source_changed=False,native_build_invoked=False)
(R/'evidence/linux-qa.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
'''
r=remote.run(s);(R/'evidence/linux-qa.json').write_text(r);print(r)
