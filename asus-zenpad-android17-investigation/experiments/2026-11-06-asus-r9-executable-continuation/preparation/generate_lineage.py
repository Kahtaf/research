from pathlib import Path
import remote,base64,json
R=Path(__file__).resolve().parents[1]
files={str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode() for p in (R/'scripts').glob('*.py') if p.name in ['native_state.py','frozen_channel.py','graph_context.py','cache_lineage.py']}
files['inputs/parent-bpf-qualified-baseline-classification.json']=base64.b64encode((R/'inputs/parent-bpf-qualified-baseline-classification.json').read_bytes()).decode()
s='FILES='+repr(files)+'\n'+r'''
from pathlib import Path
import os,resource,signal,base64,json,re,sys,hashlib,shlex
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(240,240));resource.setrlimit(resource.RLIMIT_FSIZE,(512*1024**2,512*1024**2));signal.alarm(300)
R=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1');F=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1-fixtures');A=Path('/srv/android/lineage24');O=Path('/srv/android/asus-reviewed-build-kit/r8');B=Path('/srv/android/asus-reviewed-build-kit/r9')
for rel,b in FILES.items():
 p=R/rel
 if p.exists():p.write_bytes(base64.b64decode(b))
 else:
  with p.open('xb') as f:f.write(base64.b64decode(b))
sys.path.insert(0,str(R/'scripts'))
from native_state import selected_state,selected_deps,artifact,sha
from graph_context import module_identity,module_block,variant_text,parse,kati_edges,hash_bytes
from frozen_channel import phases,execution
from cache_lineage import file_pin,SCHEMA,METHOD_SHA,BASELINE_METHOD_SHA,verify_method
plan=json.loads((R/'inputs/plan.json').read_text());verify_method(plan)
review=json.loads((R/'inputs/method-review/relational-lineage.json').read_text())
prior=set(json.loads((B/'evidence/selected-siso-state-v2.json').read_text())['selected_entries'])|{row['output'] for row in review['rows']}
qualified=json.loads(Path(plan['bpf_qualified_selection']).read_text());qrows={row['graph_output_chain'][-1]:row for row in qualified['objects']}
baseline=set(qrows)-prior;targets=prior|baseline
assert len(prior)==38 and len(baseline)==23 and len(targets)==61
states=selected_state(A,targets);deps=selected_deps(A,targets);bundle=phases(O,targets)
hints=json.loads((R/'inputs/method-review/selected-soong-modules.json').read_text())['modules']
module_names={module_identity(t)['module'] for t in targets if module_identity(t)}
modules={}
for name in sorted(module_names):
 h=hints.get(name)
 if h:h=dict(h,sha256=hash_bytes(h['text'].encode()))
 modules[name]=module_block(A,name,h)
 (F/'map-progress.json').write_text(json.dumps(dict(stage='modules',done=len(modules),total=len(module_names),last=name)))
installed={t for t in prior if t.startswith('out/target/product/')}
installed|={'out/target/product/p00a/'+p for p in ['system/vendor/lib64/hw/sensors.mt8163.so','system/vendor/lib64/hw/ACCOUNT_REDACTED','system/vendor/bin/hw/android.hardware.sensors@1.0-service']}
installed|={row['graph_output_chain'][0] for row in qualified['objects'] if row['install_path'].startswith('system/')}
kati=kati_edges(A,installed)
with (A/'out/soong/build.lineage_p00a.ninja').open('rb') as f:prelude=f.read(110000)
_,rules,globals_=parse(prelude.decode())
catalog=dict(modules=modules,kati=kati,global_prefix=dict(path='out/soong/build.lineage_p00a.ninja',offset=0,bytes=len(prelude),sha256=hash_bytes(prelude)),rules=rules)
pin_cache={}
def pin(rel):
 if rel not in pin_cache:pin_cache[rel]=file_pin(A/rel)
 return pin_cache[rel]
def regular(rel):
 return rel and '$' not in rel and not Path(rel).is_absolute() and '..' not in Path(rel).parts and (A/rel).is_file()
def source_like(rel):return rel.endswith(('.c','.cc','.cpp','.rs','.h','.hpp','.bp','.bpf'))
def expand(value,variables,depth=0):
 if depth>20:raise ValueError('Ninja variable cycle')
 sentinel='\x00DOLLAR\x00';value=value.replace('$$',sentinel)
 def repl(m):
  key=m[1] or m[2]
  if key not in variables:raise ValueError('Unresolved Ninja variable: '+key)
  return expand(variables[key],variables,depth+1)
 return re.sub(r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_.-]*)',repl,value).replace(sentinel,'$')
records={};prepared=[]
for target in sorted(targets):
 identity=module_identity(target)
 if identity:
  name=identity['module'];variant=identity['variant'];block=modules[name];vt=variant_text(block['text'],name,variant);edges,_,vars_=parse(vt);edge=edges[target]
  defined=re.search(r'^# Defined: ([^\n]+)',vt,re.M)[1].split(':',1)[0]
  sources=sorted({p for e in edges.values() for p in e['inputs'] if regular(p) and source_like(p)})
  ctx=dict(kind='SOONG_MODULE',module=name,variant=variant,definition=defined,variant_sha256=hash_bytes(vt.encode()),edge_sha256=hash_bytes(edge['text'].encode()))
  rule=rules[edge['rule']];variables=dict(globals_,**vars_);variables.update(edge['variables']);variables.update(out=' '.join(edge['outputs']),**{'in':' '.join(edge['explicit_inputs'])})
 else:
  name=Path(target).name;variant='android_arm64_armv8-a';name='bpfloader' if name=='bpfloader' else 'vold';block=modules[name]
  vt=variant_text(block['text'],name,variant);edges,_,vars_=parse(vt);defined=re.search(r'^# Defined: ([^\n]+)',vt,re.M)[1].split(':',1)[0]
  sources=sorted({p for e in edges.values() for p in e['inputs'] if regular(p) and source_like(p)})
  edge=parse(kati[target]['text'])[0][target];rule=list(parse(kati[target]['rule_text'])[1].values())[0]
  variables=dict(globals_,**vars_);variables.update(edge['variables']);variables.update(out=target,**{'in':' '.join(edge['explicit_inputs'])})
  ctx=dict(kind='KATI_INSTALL',module=name,variant=variant,definition=defined)
 source_relations=[p for p in edge['inputs'] if regular(p) and source_like(p)]
 if not source_relations:source_relations=[p for p in sources if not p.startswith('out/') and not p.endswith(('.h','.hpp','.bp'))]
 source_pins={p:pin(p) for p in sources};source_pins[defined]=pin(defined)
 rsp_candidates=[]
 pattern=rule['variables'].get('rspfile')
 if pattern:
  try:rsp_candidates.append(expand(pattern,variables))
  except ValueError:pass
 for x in [target+'.rsp',target+'.clang.rsp']:
  if regular(x):rsp_candidates.append(x)
 rsp_candidates=list(dict.fromkeys(rsp_candidates))
 state=states.get(target);actual=artifact(A/target)
 if state:
  assert state['digest']['hash']==actual['sha256'] and state['digest']['size_bytes']==actual['bytes'] and state['mtime_ns']==actual['mtime_ns'],target
 if target in prior:
  assert state is not None,target
  candidates=[execution(p,target,state['cmd_hash_hex'],A,rsp_candidates) for p in bundle if target in p['metrics']]
  candidates=[x for x in candidates if x is not None];assert len(candidates)==1,(target,len(candidates));executed=candidates[0]
  command=executed['verbose']['command'];kind='PRIOR_R8_EXECUTION'
 else:
  executed=None;kind='QUALIFIED_BASELINE_ARTIFACT'
  assert actual['sha256']==qrows[target]['sha256'] and actual.get('elf_machine')==247,target
  try:command=expand(rule['variables']['command'],variables)
  except ValueError:command=''
 response_pins={p:pin(p) for p in rsp_candidates if regular(p)}
 literals=set(p for p in edge['inputs'] if regular(p) and p!=target)
 if command:
  for token in shlex.split(command):
   value=token.removeprefix('@');pieces=[value]
   if '=' in value:pieces.append(value.rsplit('=',1)[-1])
   for piece in pieces:
    if regular(piece) and piece!=target:literals.add(piece)
 for p in response_pins:
  for token in shlex.split((A/p).read_text()):
   if regular(token) and token!=target:literals.add(token)
 dep_record=deps.get(target)
 if dep_record:
  assert dep_record['mtime_ns']==actual['mtime_ns'],target
  for p in dep_record['dependencies']:
   if regular(p):literals.add(p)
  dep_evidence=dict(kind='GCC_DEPSLOG',record=dep_record,historical_input_tree_attested=False)
 else:
  depfiles=[p for p in [target+'.d',str(Path(target).with_suffix('.d'))] if regular(p)]
  for p in depfiles:
   for token in (A/p).read_text().replace('\\\n',' ').split():
    if regular(token):literals.add(token)
  dep_evidence=dict(kind='DEPFILE' if depfiles else 'GRAPH_AND_RSP',files={p:pin(p) for p in depfiles},historical_input_tree_attested=False)
 # Source and toolchain pins bind the admitted cohort. Other current input pins
 # detect changes for prior reuse; a real CURRENT_EXECUTION can replace them.
 toolchain={p:pin(p) for p in literals if p.startswith(('prebuilts/','out/host/','build/soong/')) and not source_like(p)}
 for compiler in ['prebuilts/clang/host/linux-x86/clang-r584948b/bin/clang++','prebuilts/clang/host/linux-x86/clang-r584948b/bin/clang','prebuilts/clang/host/linux-x86/clang-r584948b/bin/ld.lld']:
  if regular(compiler):toolchain[compiler]=pin(compiler)
 if name=='bpfloader':
  p='prebuilts/rust-toolchain/linux-x86/1.93.1/bin/rustc';toolchain[p]=pin(p)
 row=dict(schema=SCHEMA,output=target,provenance_kind=kind,module=name,variant=variant,graph_context=ctx,module_sources=sources,source_relations=source_relations,source_pins=source_pins,toolchain_pins=toolchain,response_pins=response_pins,input_pins={p:pin(p) for p in sorted(literals) if p not in source_pins and p not in toolchain and p not in response_pins},rsp_candidates=rsp_candidates,dependency_evidence=dep_evidence,native_state=state,artifact=actual,execution=executed,command_hash_hex=state['cmd_hash_hex'] if state else None,input_observation_scope='CURRENT_CONTROLLED_CUSTODY_EPOCH_NOT_UNCONDITIONAL_HISTORICAL_ATTESTATION',runtime_requalification_required=target in qrows and target in prior)
 if target in baseline:row['qualified_sha256']=qrows[target]['sha256']
 records[target]=row
 (F/'map-progress.json').write_text(json.dumps(dict(stage='records',done=len(records),total=len(targets),last=target)))
matrix=[]
for target,q in qrows.items():
 row=records[target]
 matrix.append(dict(output=target,install_path=q['install_path'],kind=row['provenance_kind'],qualification_row=q,qualification_row_sha256=hashlib.sha256(json.dumps(q,sort_keys=True,separators=(',',':')).encode()).hexdigest(),qualified_sha256=q.get('sha256'),current_sha256=row['artifact']['sha256'],source_pins=row['source_pins'],module=row['module'],variant=row['variant'],native_command_hash=row['command_hash_hex'],execution=row['execution'],runtime_requalification_required=row['runtime_requalification_required'],host_checks_scope='ELF/compiler/graph/installed SYSTEM-or-APEX byte identity; no kernel/runtime qualification'))
classification=dict(schema='bpf-23-3-26-classification/v1',qualification_sha256=sha(plan['bpf_qualified_selection']),baseline_method_sha256=BASELINE_METHOD_SHA,rows=matrix)
lineage=dict(schema=SCHEMA,parent_method_sha256=METHOD_SHA,r8_kit_seal='f55aedf8ac9d2a513e3663230db0b9d802e72b5df512fc0db6b3714331a7efa4',r8_phase_pins={Path(p['folder']).name:p['receipt_sha256'] for p in bundle},prior_output_allowlist=sorted(prior),baseline_output_allowlist=sorted(baseline),failed_r8_full_phase_is_product_success=False,records=records,graph_catalog=catalog,trust_model='controlled-tree/native-incremental',historical_all_input_bytes_attested=False,current_native_validation_required=True)
for name,data in [('native-lineage-map.json',lineage),('bpf-classification.json',classification)]:
 with (R/'inputs'/name).open('x') as f:json.dump(data,f,indent=2,sort_keys=True);f.write('\n')
assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<256*1024**2
r=dict(prior_outputs=len(prior),qualified_baseline_outputs=len(baseline),bpf_rows=len(matrix),source_module_groups=len(modules),native_state_records=len(states),lineage_map_sha256=sha(R/'inputs/native-lineage-map.json'),bpf_matrix_sha256=sha(R/'inputs/bpf-classification.json'),current_native_validation=False,active_source_changed=False)
with (R/'evidence/map-generation.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);(R/'evidence/map-generation.json').write_text(r);print(r)
