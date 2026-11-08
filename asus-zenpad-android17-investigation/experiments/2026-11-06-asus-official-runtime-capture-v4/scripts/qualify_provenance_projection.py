"""Read-only graph path projection of capture.provenance; never inspect payloads."""
import hashlib,json,os,resource,sqlite3,sys,time
from collections import deque
from pathlib import Path
ROOT=Path('/srv/android/asus-official-runtime-capture/preparation-v4')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(180,180))
sys.path.insert(0,str(ROOT/'source'))
from graph import Graph
from safeio import Tree,need,permitted,Refusal,write_json
start=time.monotonic();work=ROOT/'graph-provenance-004';work.mkdir(mode=0o700)
full=json.loads((ROOT/'graph-qualification-003/qualification.json').read_bytes());profile=json.loads((ROOT/'inputs/profile-r8.json').read_bytes());selector=json.loads((ROOT/'inputs/selector.json').read_bytes())
need(all('error' not in x for x in full['selector_producer_resolutions']),'GRAPH_UNKNOWN','known selector producer')
need(full['source_before']==full['source_after'],'DRIFT','actual source hash bindings')
need(full['tested_module_sha256']['graph.py']==hashlib.sha256((ROOT/'source/graph.py').read_bytes()).hexdigest(),'DRIFT','tested graph module')
g=Graph.__new__(Graph);g.tree=Tree(ROOT/'graph-qualification-003/frozen');g.paths=list(full['frozen']);g.limits=profile['limits'];g.pins=full['frozen'];g.records={};g.evidence_bytes=0
g.db=sqlite3.connect('file:'+str(ROOT/'graph-qualification-003/graph-index.sqlite')+'?mode=ro&immutable=1',uri=True);g.db.execute('PRAGMA cache_size=-8192')
g.recheck()
product='out/target/product/p00a/'
installed={product+p for p in selector['required']}
# Graph targets under all selected metadata trees are candidates, not proof that
# any output exists. This includes complete policy graph groups without opening them.
for item in selector['trees']:
 prefix=product+item['path']+'/'
 for (name,) in g.db.execute("SELECT name FROM blocks WHERE kind='edge' AND name>=? AND name<?",(prefix,prefix+'\uffff')):
  installed.add(name);need(len(installed)<=profile['limits']['files'],'COUNT','graph-only installed candidates')
queue=deque((p,0) for p in sorted(installed));queue.extend((p,0) for p in selector['generation_outputs'].values())
edges={};errors=[];excluded=0;leaves=set();public_dependencies=set()
while queue:
 path,depth=queue.popleft()
 if path in edges:continue
 need(depth<30 and len(edges)<profile['limits']['edges'],'GRAPH_DEPTH',path)
 try:
  edge=g.edge(path);edges[path]=edge
  need(edge['rule']!='phony','UNKNOWN_SELECTED_OUTPUT',path)
  real=[d['path'] for d in edge['dependencies'] if d['kind']=='explicit' and '/' in d['path']]
  if path in installed:
   need(len(real)==1,'INSTALL_SOURCE',path)
   permitted(real[0]);public_dependencies.add(real[0])
   if g.has_edge(real[0]):queue.append((real[0],depth+1))
   else:leaves.add(real[0])
  package=path.endswith(('.apex','.capex','.apex.unsigned'))
  metadata=any(t in path for t in ('/selinux/','/sepolicy/','/vintf/','/linkerconfig/','build.prop','apexkeys.txt','api_fingerprint','product_config'))
  for dep in edge['dependencies']:
   name=dep['path']
   if dep['kind'] in ('order_only','validation'):continue
   if '/' not in name:
    need(g.has_edge(name) and g.edge(name)['rule']=='phony','GRAPH_PSEUDO_UNKNOWN',name)
    continue
   try:permitted(name)
   except Refusal:excluded+=1;continue
   if metadata or package:
    public_dependencies.add(name)
    if g.has_edge(name) and (metadata or name.endswith(('.apex','.capex','.apex.unsigned'))):queue.append((name,depth+1))
   elif name in real and '/unstripped/' in name and g.has_edge(name):
    public_dependencies.add(name);queue.append((name,depth+1))
 except (Refusal,ValueError) as error:
  errors.append({'path':path,'error':str(error)})
g.recheck();g.close();g.tree.close()
u=resource.getrusage(resource.RUSAGE_SELF)
r={'schema':1,'status':'PASS' if not errors else 'GRAPH_RESOLUTION_BLOCKER','scope':'graph-path-projection-only-no-payload-acceptance','actual_select_verify_copy':False,'actual_payload_files_opened':False,'all_known_selector_producers_resolved':True,'installed_graph_candidate_count':len(installed),'resolved_edge_count':len(edges),'public_dependency_path_count':len(public_dependencies),'excluded_private_or_image_path_count':excluded,'source_leaf_count':len(leaves),'errors':errors,'recorded_evidence_bytes':g.evidence_bytes,'full_resource_receipt_sha256':hashlib.sha256((ROOT/'graph-qualification-003/qualification.json').read_bytes()).hexdigest(),'capture_traversal_sha256':hashlib.sha256((ROOT/'source/capture.py').read_bytes()).hexdigest(),'graph_module_sha256':hashlib.sha256((ROOT/'source/graph.py').read_bytes()).hexdigest(),'elapsed_seconds':round(time.monotonic()-start,3),'cpu_seconds':round(u.ru_utime+u.ru_stime,3),'max_rss_KiB':u.ru_maxrss,'cpu_count':len(os.sched_getaffinity(0)),'address_space_limit_bytes':1024**3,'cpu_seconds_limit':180,'wall_seconds_limit':300,'payload_hash_equality_ELF_policy_APEX_validation':False}
write_json(work/'qualification.json',r);print(json.dumps(r,indent=2));raise SystemExit(0 if not errors else 1)
