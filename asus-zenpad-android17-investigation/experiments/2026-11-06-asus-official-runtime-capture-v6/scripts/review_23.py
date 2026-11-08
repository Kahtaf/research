"""Finite synthetic review cases; never execute Ninja/resolvers or inspect real state."""
import copy,hashlib,json,os,resource,struct,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'source')]
from test_capture import Fixture,TMP,PRODUCT,encoded
from test_provenance import SmallGraph,aggregate_fixture
from test_metadata_roles import MetadataFixture
from safeio import Refusal,sha
from provenance import copy_source,aggregate_plan,bind_aggregate
import metadata_roles as m
import capture
assert sys.platform=='linux'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(120,120))
CASES=[]
def case(name,fn,expected):
    start=time.monotonic()
    try:observed=fn()
    except Exception as e:observed={'status':'refused','code':getattr(e,'code',type(e).__name__),'detail':str(e)}
    ok=expected(observed)
    CASES.append({'name':name,'expectation_met':ok,'observed':observed,'seconds':round(time.monotonic()-start,4)})
def refused(x):return x.get('status')=='refused'
def accepted(x):return x.get('status')=='accepted'
def graph_case(text,extras=None,target='out/a'):
    with tempfile.TemporaryDirectory(dir=TMP) as d:
        f=SmallGraph(d,text,extras)
        try:
            e=f.graph.edge(target);source=copy_source(e)
            return {'status':'accepted','command':e['command'],'source':source,'rule_bindings':e['rule_bindings'],'matching_edge_records':len(f.graph.rows('edge',target))}
        finally:f.close()
cp='rule cp\n  command = cp $in $out\n'
case('file_command_overrides_rule_without_build_environment',lambda:graph_case('command = echo unreviewed-producer\n'+cp+'build out/a: cp src/a\n'),refused)
case('edge_environment_keeps_rule_precedence_over_parent_command',lambda:graph_case('command = echo parent\n'+cp+'build out/a: cp src/a\n  unused = value\n'),accepted)
case('identical_duplicate_edges_same_file_are_ambiguous',lambda:graph_case(cp+'build out/a: cp src/a\nbuild out/a: cp src/a\n'),refused)
case('identical_duplicate_edges_different_scopes_are_ambiguous',lambda:graph_case(cp+'build out/a: cp src/a\nsubninja out/child.ninja\n',{'child.ninja':'rule cp\n  command = arbitrary-generator $in $out\nbuild out/a: cp src/a\n'}),refused)
case('nonidentical_duplicate_edges_refuse',lambda:graph_case(cp+'build out/a: cp src/a\nbuild out/a: cp src/b\n'),refused)
case('nonempty_rule_dyndep_must_refuse_unsupported_semantics',lambda:graph_case('rule cp\n  command = cp $in $out\n  dyndep = out/extra.dd\nbuild out/a: cp src/a || out/extra.dd\n'),refused)
case('nonempty_edge_dyndep_must_refuse_unsupported_semantics',lambda:graph_case(cp+'build out/a: cp src/a || out/extra.dd\n  dyndep = out/extra.dd\n'),refused)
case('unknown_selected_rule_refuses',lambda:graph_case('build out/a: unknown src/a\n'),refused)
case('wrong_copy_command_source_refuses',lambda:graph_case('rule cp\n  command = cp src/spoof $out\nbuild out/a: cp src/a\n'),refused)

def full_command_spoof():
    with tempfile.TemporaryDirectory(dir=TMP) as d:
        f=Fixture(d);f.graph.write_text('command = echo unreviewed-producer\n'+f.graph.read_text())
        result=f.run();selection=json.loads((f.output('select-1')/'selection.json').read_bytes())
        edge=selection['edges'][PRODUCT+'system/bin/init']
        return {'status':'accepted','capture_status':result['status'],'observed_command':edge['command'],'classification':edge['producer_classification'],'runtime_ready':result['runtime_ready']}
case('complete_fixture_wrong_effective_file_command',full_command_spoof,refused)

def metadata_case(mutate=None):
    with tempfile.TemporaryDirectory(dir=TMP) as d:
        f=MetadataFixture(d)
        try:
            if mutate:mutate(f)
            roles=m.collect(f,ROOT,host_exists=lambda _:False)
            return {'status':'accepted','states':[(r['slot'],r['state'],r['bytes']) for r in roles['search_slots']],'production_admission':roles['production_admission'],'native_metadata_admitted':roles['native_metadata_admitted'],'native_query_executed':roles['native_query_executed']}
        finally:f.close()
def wrong_complete(f):
    p=f.kit/'attempt/validation/complete.json';v=json.loads(p.read_bytes());v.pop('host_metadata_source_plan_sha256');p.write_bytes(encoded(v))
def wrong_content_binding(f):
    p=f.kit/'attempt/validation/complete.json';v=json.loads(p.read_bytes());v['installed_four_content_receipt_sha256']='0'*64;p.write_bytes(encoded(v))
def symlink_slot(f):
    p=Path(f.plan['search_slots'][0]['origin']);p.unlink();p.symlink_to(f.aosp/'public-target')
    (f.aosp/'public-target').write_bytes(b'')
def symlink_context(f):
    p=Path(f.plan['contexts']['origin']);data=p.read_bytes();p.unlink();q=f.aosp/'public-context';q.write_bytes(data);p.symlink_to(q)
def oversized_slot(f):
    row=f.plan['search_slots'][0];data=b'x'*(1024**2+1);Path(row['origin']).write_bytes(data);row['sha256']=sha(data);f.refresh()
def wrong_absence(f):f.plan['search_slots'][1]['absence_attestation_sha256']='0'*64;f.refresh()
def tiny_compiled(f):
    data=bytes.fromhex('8aff7cf9');Path(f.plan['contexts']['origin']).write_bytes(data);f.plan['contexts']['sha256']=sha(data);f.refresh()
case('present_empty_and_absence_remain_distinct',lambda:metadata_case(),lambda x:accepted(x) and x['states'][0][1:] == ('present',0) and x['states'][1][1:] == ('absent',None) and not x['native_query_executed'])
case('validator_plan_binding_cannot_be_omitted',lambda:metadata_case(wrong_complete),refused)
case('validator_installed_four_binding_cannot_be_spoofed',lambda:metadata_case(wrong_content_binding),refused)
case('present_slot_symlink_refuses',lambda:metadata_case(symlink_slot),refused)
case('compiled_context_symlink_refuses',lambda:metadata_case(symlink_context),refused)
case('slot_one_MiB_ceiling_refuses',lambda:metadata_case(oversized_slot),refused)
case('absence_attestation_spoof_refuses',lambda:metadata_case(wrong_absence),refused)
case('compiled_magic_is_only_preparation_guard',lambda:metadata_case(tiny_compiled),lambda x:accepted(x) and not x['native_metadata_admitted'] and not x['production_admission'])

def graft_metadata(f,context_rule='cp'):
    f.selector['host_metadata_reference_sha256']=json.loads((ROOT/'inputs/selector.json').read_bytes())['host_metadata_reference_sha256']
    # Bind synthetic actual installed-four content to the existing qualified fixture validator.
    for path in ('system/bin/run-as','system/vendor/etc/selinux/vendor_file_contexts'):
        data=b'public role fixture\n';source='src/'+Path(path).name
        f.put('aosp',PRODUCT+path,data);f.put('aosp',source,data)
        with f.graph.open('a') as out:out.write('build '+PRODUCT+path+': cp '+source+'\n')
    plan={'schema':m.PLAN_SCHEMA,'build_id':f.profile['revision'],'source_binding_sha256':f.digest('kit','attempt/validation/source-postimages.json'),'tool_group_sha256':m.GROUP,'native_target_out':f.profile['product_out']+'/system/','search_root':f.profile['product_out'],'search_slots':[],'contexts':{},'installed_content_receipt':{}}
    for slot in m.SLOTS:
        origin=f.profile['product_out']+'/'+slot+'/etc/fs_config_files';row={'slot':slot,'state':'absent','origin':origin,'sha256':None,'absence_attestation_sha256':sha(m.encoded({'build_id':plan['build_id'],'source_binding_sha256':plan['source_binding_sha256'],'slot':slot,'origin':origin,'state':'absent'}))}
        if slot=='system':
            f.put('aosp',PRODUCT+slot+'/etc/fs_config_files',b'');f.put('aosp','src/empty-slot',b'')
            with f.graph.open('a') as out:out.write('build '+PRODUCT+slot+'/etc/fs_config_files: cp src/empty-slot\n')
            row.update(state='present',sha256=sha(b''),absence_attestation_sha256=None)
        plan['search_slots'].append(row)
    context=PRODUCT+'obj/ETC/final/file_contexts.bin';data=bytes.fromhex('8aff7cf9')+b'fixture compiled-format placeholder'
    f.put('aosp',context,data);f.put('aosp','src/context-source',data)
    with f.graph.open('a') as out:out.write('build '+context+': '+context_rule+' src/context-source\n')
    plan['contexts']={'format':'compiled','origin':f.profile['aosp']+'/'+context,'sha256':sha(data)}
    plan['installed_content_receipt']={'schema':m.RECEIPT_SCHEMA,'build_id':plan['build_id'],'source_binding_sha256':plan['source_binding_sha256'],'files':[{'path':p,'sha256':f.digest('aosp',PRODUCT.rstrip('/')+p),'bytes':(f.root/'aosp'/(PRODUCT.rstrip('/')+p)).stat().st_size} for p in m.FOUR]}
    raw=encoded(plan);f.put('kit',m.PLAN,raw);f.profile['host_metadata_source_plan_sha256']=sha(raw)
    f.validation.update(host_metadata_source_plan_sha256=sha(raw),installed_four_content_receipt_sha256=sha(m.encoded(plan['installed_content_receipt'])))
    f.put('kit','attempt/validation/complete.json',encoded(f.validation))
    return plan

def integration(kind):
    with tempfile.TemporaryDirectory(dir=TMP) as d:
        f=Fixture(d);graft_metadata(f,'generate' if kind=='unknown-context' else 'cp')
        if kind=='failed-terminal':f.put('logs','full-build-r8.exit-code',b'1\n')
        if kind=='unbound-content':
            del f.validation['installed_four_content_receipt_sha256'];f.put('kit','attempt/validation/complete.json',encoded(f.validation))
        collect=m.collect;recheck=m.recheck;calls=[]
        def wrapped(*args):calls.append('collect');return collect(*args,host_exists=lambda _:False)
        with patch.object(m,'collect',wrapped),patch.object(m,'recheck',lambda *args:recheck(*args,host_exists=lambda _:False)):
            try:
                result=f.run();selected=json.loads((f.output('select-1')/'selection.json').read_bytes())
                if kind=='copy':
                    f.run('copy','copy-1',selected)
                    copies=json.loads((f.output('copy-1')/'COMPLETE.json').read_bytes())['copies']
                    empty=next(r for r in copies if r.get('path')==PRODUCT+'system/etc/fs_config_files')
                    assert empty['bytes']==0 and empty['before']==empty['copy']==empty['after']==sha(b'')
                return {'status':'accepted','capture_status':result['status'],'roles':selected['host_metadata_capture'],'calls':calls}
            except Exception as e:
                return {'status':'refused','code':getattr(e,'code',type(e).__name__),'detail':str(e),'calls':calls}
case('full_roles_empty_copy_retains_nonadmission',lambda:integration('copy'),lambda x:accepted(x) and not x['roles']['production_admission'] and not x['roles']['query_layout_materialized'])
case('failed_terminal_precedes_metadata_collection',lambda:integration('failed-terminal'),lambda x:refused(x) and x['code']=='TERMINAL_FAILED' and x['calls']==[])
case('full_roles_unbound_content_refuses',lambda:integration('unbound-content'),lambda x:refused(x) and x['code']=='METADATA_BINDING')
case('full_roles_unknown_compiled_context_producer_refuses',lambda:integration('unknown-context'),lambda x:refused(x) and x['code']=='PRODUCER_COMMAND')

def aggregate_changed_order():
    with tempfile.TemporaryDirectory(dir=TMP) as d:
        f,state,contract,e=aggregate_fixture(d)
        try:
            p=aggregate_plan(f.graph,e,contract);p['inputs'][0],p['inputs'][1]=p['inputs'][1],p['inputs'][0]
            bind_aggregate(state,e,p);return {'status':'accepted'}
        finally:f.close()
case('aggregate_streamed_byte_order_remains_bound',aggregate_changed_order,lambda x:refused(x) and x['code']=='GENERATION_BYTES')
receipt={'schema':1,'fixture_only':True,'production_state_read':False,'native_engines_executed':False,'local_production_changes':False,'tests_run':len(CASES),'expectations_met':sum(x['expectation_met'] for x in CASES),'unmet_expectations':[x['name'] for x in CASES if not x['expectation_met']],'cases':CASES}
with (ROOT/'evidence'/str(os.environ.get('V6_CASE_LABEL','review-23')+'.json')).open('x') as output:
    output.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='cases'}))
# V6 requires every corrected independent expectation to hold.
raise SystemExit(0 if not receipt['unmet_expectations'] else 1)
