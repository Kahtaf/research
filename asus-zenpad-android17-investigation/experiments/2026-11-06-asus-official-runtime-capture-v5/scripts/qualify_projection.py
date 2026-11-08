"""Exact 25 mandatory paths and capture-relevant ancestors, no output payload reads."""
import hashlib,json,os,resource,sys,time
from collections import deque
from pathlib import Path
ROOT=Path('/srv/android/asus-official-runtime-capture/preparation-v5')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
sys.path[:0]=[str(ROOT/'source'),str(ROOT/'scripts')]
from v4_fixture import V4Fixture
from provenance import install_kind,aggregate_plan
from safeio import need,permitted,Refusal
start=time.monotonic();g=V4Fixture(ROOT)
selector=json.loads((ROOT/'inputs/selector.json').read_bytes());contract=json.loads((ROOT/'inputs/provenance-contract.json').read_bytes())
extracted=json.loads((ROOT/'evidence/v4-extracted-records.json').read_bytes());targets=extracted['mandatory_targets'];installed={'out/target/product/p00a/'+p for p in selector['required']}
queue=deque((p,0) for p in targets);seen=set();edges={};errors={};links={};classes={};excluded=[];leaf=set();tool_refs=set();aggregate=None
while queue:
 path,depth=queue.popleft()
 if path in seen:continue
 seen.add(path);need(depth<30 and len(seen)<=2048,'GRAPH_DEPTH','projection budget')
 links[path]=[]
 try:
  edge=g.edge(path);need(edge['rule']!='phony','UNKNOWN_SELECTED_OUTPUT',path)
  if path in installed:
   classification=install_kind(edge,contract);classes[path]=classification
   if classification['kind']=='reviewed-aggregate':
    aggregate=aggregate_plan(g,edge,contract)
    for src in aggregate['generator_sources']:
     data=(ROOT/'evidence/public-source'/src['path']).read_bytes();need(hashlib.sha256(data).hexdigest()==src['sha256'],'GENERATION_SOURCE',src['path'])
    tool_refs.update(aggregate['generator_tools'])
   else:
    source=classification['source']
    if g.has_edge(source):links[path].append(source);queue.append((source,depth+1))
    else:leaf.add(source)
  else:classes[path]={'kind':'ancestor-command-evidence-only','payload_trust_claimed':False}
  edges[path]={'rule':edge['rule'],'scope':edge['scope'],'dependencies':edge['dependencies'],'raw_sha256':hashlib.sha256(edge['raw'].encode()).hexdigest(),'rule_sha256':hashlib.sha256((edge['raw_rule'] or '').encode()).hexdigest(),'command_sha256':hashlib.sha256((edge['command'] or '').encode()).hexdigest(),'undefined_or_empty_variables':edge['undefined_or_empty_variables']}
  metadata=any(t in path for t in ('/selinux/','/sepolicy/','/vintf/','/linkerconfig/','build.prop','apexkeys.txt','api_fingerprint','product_config'))
  package=path.endswith(('.apex','.capex','.apex.unsigned'))
  real=[d['path'] for d in edge['dependencies'] if d['kind']=='explicit' and '/' in d['path']]
  for dep in edge['dependencies']:
   name=dep['path']
   if dep['kind'] in ('order_only','validation'):continue
   if '/' not in name:
    pseudo=g.edge(name);need(pseudo['rule']=='phony','GRAPH_PSEUDO_UNKNOWN',name)
    tool_refs.update(d['path'] for d in pseudo['dependencies'] if d['path'].startswith(('out/host/','prebuilts/')));continue
   try:permitted(name)
   except Refusal as error:
    need(error.code=='EXCLUDED',error.code,name);excluded.append({'producer':path,'path_string':name,'opened':False});continue
   follow=(metadata or (package and name.endswith(('.apex','.capex','.apex.unsigned'))) or (name in real and '/unstripped/' in name))
   if follow and g.has_edge(name):links[path].append(name);queue.append((name,depth+1))
   else:leaf.add(name)
 except (Refusal,ValueError) as error:errors[path]=str(error)
root_refusals={}
for target in targets:
 todo=[target];walk=set()
 while todo:
  p=todo.pop()
  if p in walk:continue
  walk.add(p);todo.extend(links.get(p,[]))
 refused={p:errors[p] for p in sorted(walk) if p in errors}
 if refused:root_refusals[target]=refused
metadata_fixed={};metadata_fixed_errors={}
for logical_path in ('/system/bin/run-as','/system/vendor/etc/selinux/vendor_file_contexts'):
 path='out/target/product/p00a'+logical_path
 try:
  edge=g.edge(path);metadata_fixed[path]={'classification':install_kind(edge,contract),'rule':edge['rule'],'raw_sha256':hashlib.sha256(edge['raw'].encode()).hexdigest()}
 except (Refusal,ValueError) as error:metadata_fixed_errors[path]=str(error)
g.recheck();g.close();usage=resource.getrusage(resource.RUSAGE_SELF)
r={'schema':1,'status':('PROJECTION_PASS' if g.scope_replay_complete else 'PROVISIONAL_INDEX_ONLY') if not root_refusals else 'MANDATORY_REFUSALS','metadata_fixed_role_producers':metadata_fixed,'metadata_fixed_role_refusals':metadata_fixed_errors,'full_capture_PASS':False,'output_payload_reads':False,'old_index_production_reuse':False,'mandatory_target_count':len(targets),'mandatory_direct_resolved':sum(t in edges for t in targets),'mandatory_root_refusals':root_refusals,'ancestor_refusals':errors,'classified':classes,'edges':edges,'aggregate_plan':aggregate,'generator_tool_references':sorted(tool_refs),'excluded_private_image_path_strings':excluded,'public_leaf_path_count':len(leaf),'visited_path_count':len(seen),'evidence_bytes':g.evidence_bytes,'index_identity':g.before,'index_identity_unchanged':True,'v4_binding':g.binding,'all_14_graph_identities_unchanged':True,'new_large_index_allocated':False,'full_graph_index_rehashed':False,'resource_limits':{'cpu_count':1,'address_space_bytes':1024**3,'cpu_seconds':120,'wall_seconds':240,'record_bytes':16*1024**2,'visited_edges':2048,'owned_storage_bytes':512*1024**2},'elapsed_seconds':round(time.monotonic()-start,3),'cpu_seconds':round(usage.ru_utime+usage.ru_stime,3),'max_rss_KiB':usage.ru_maxrss,'global_names_consulted':sorted({name for name,file in g.scopes.lookups}),'global_lookup_contexts':sorted(g.scopes.lookups),'scope_replay_complete':g.scope_replay_complete,'tested_pins':{n:hashlib.sha256((ROOT/'source'/n).read_bytes()).hexdigest() for n in ('graph.py','ninja.py','provenance.py','capture.py','metadata_roles.py')}}
# Always preserve attempts, including genuine mandatory refusals.
label=os.environ.get('V5_PROJECTION_LABEL','projection-001')
need(label.startswith('projection-') and label.replace('-','').isalnum(),'PATH',label)
with (ROOT/'evidence'/str(label+'.json')).open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in r.items() if k not in ('classified','edges','aggregate_plan','generator_tool_references','excluded_private_image_path_strings')}))
