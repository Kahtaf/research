"""Explicit native lineage under the parent's controlled incremental method."""
import json
from pathlib import Path
import sys
from frozen_channel import phases, execution, require_current_closure
from graph_context import validate_context, hash_bytes
from native_state import selected_state, selected_deps, artifact, sha

METHOD_SHA='202562e1b98a0d9de47f9896b755be10957984c7812d1b9268d3052201cee3ad'
BASELINE_METHOD_SHA='b582731ad51c8308f03796fbae39875ba1d8b1fdaa5b3fcc70ebee7be6a29bfb'
RUNTIME_CONDITIONAL_SHA='a4b790a756d92d2d656e0d45fe80dca9839bb0a381d58b647266fd11ddf379ec'
R8_SEAL='f55aedf8ac9d2a513e3663230db0b9d802e72b5df512fc0db6b3714331a7efa4'
SCHEMA='selected-native-lineage/v2'

def read(path):return json.loads(Path(path).read_text())
def need(value,message):
    if not value:raise ValueError(message)

def file_pin(path):
    path=Path(path);need(path.is_file(),'Missing bound input: '+str(path))
    return dict(sha256=sha(path),bytes=path.stat().st_size,symlink=str(path.readlink()) if path.is_symlink() else None)

def verify_method(plan):
    need(sha(plan['native_cache_method'])==METHOD_SHA,'Parent native-cache method pin changed')
    decision=read(plan['native_cache_method'])
    need(decision['method_accepted'] is True and decision['trust_model']=='controlled-tree/native-incremental','Controlled native method not accepted')
    need(not decision['r9_kit_accepted'] and not decision['r9_launch_authorized'],'Method receipt is not kit/launch acceptance')
    need(sha(plan['qualified_baseline_method'])==BASELINE_METHOD_SHA,'Parent BPF classification pin changed')
    baseline=read(plan['qualified_baseline_method'])
    need(baseline['classification_accepted'] and baseline['classification']=='QUALIFIED_BASELINE_ARTIFACT' and baseline['proposed_baseline_count']==23 and not baseline['claimed_prior_or_current_execution'],'Wrong qualified baseline classification')
    need(sha(plan['bpf_runtime_conditional_method'])==RUNTIME_CONDITIONAL_SHA,'Parent BPF conditional scope pin changed')
    conditional=read(plan['bpf_runtime_conditional_method'])
    need(conditional['decision']=='HOST_ASSEMBLY_ALLOWED_RUNTIME_ACCEPTANCE_CONDITIONAL' and conditional['runtime_accepted'] is False and conditional['physical_go'] is False,'Wrong BPF host/runtime boundary')
    need(conditional['selected_inventory_sha256']==sha(plan['bpf_qualified_selection']),'Conditional selected inventory pin changed')
    review=Path(plan['run_root'])/'inputs/method-review'
    need(sha(review/'README.md')==decision['review_report_sha256'] and sha(review/'QA.json')==decision['qa_sha256'] and sha(review/'relational-lineage.json')==decision['relational_evidence_sha256'],'Independent method evidence binding changed')
    qa=read(review/'QA.json');need(qa['all_pass'] and len(qa['evidence_files'])==20,'Independent method QA incomplete')
    for name,row in qa['evidence_files'].items():
        p=review/name;need(sha(p)==row['sha256'] and p.stat().st_size==row['bytes'],'Independent evidence drift: '+name)
    return decision

def compare_identity(observed,expected):
    """Comparison of explicit identities, never historical input-tree attestation."""
    for key in ['output','module','variant','command_hash_hex','source_pins','response_pins','graph_identity','toolchain_pins']:
        need(observed.get(key)==expected.get(key),'Native lineage identity changed: '+key)
    need(observed.get('completed') is True and observed.get('failed_action') is False,'Failed or pending native action cannot qualify')
    return True

class Session:
    def __init__(self,root,plan,current_bundle=None,state=None,dependencies=None):
        self.root=Path(root);self.plan=plan;self.aosp=Path(plan['aosp']);verify_method(plan)
        self.map=read(plan['native_lineage_map']);need(self.map['schema']==SCHEMA and self.map['parent_method_sha256']==METHOD_SHA,'Wrong native lineage map/method')
        self.rows=self.map['records'];self.catalog=self.map['graph_catalog'];self.matrix=read(plan['qualified_baseline_map'])
        need(self.matrix['runtime_conditional_method_sha256']==RUNTIME_CONDITIONAL_SHA and self.matrix['runtime_accepted'] is False,'Conditional BPF runtime boundary changed')
        need(self.matrix['qualification_sha256']==sha(plan['bpf_qualified_selection']) and self.matrix['baseline_method_sha256']==BASELINE_METHOD_SHA,'BPF qualification binding changed')
        need(len(self.matrix['rows'])==26 and sum(x['kind']=='QUALIFIED_BASELINE_ARTIFACT' for x in self.matrix['rows'])==23 and sum(x['kind']=='PRIOR_R8_EXECUTION' for x in self.matrix['rows'])==3,'Exact23/3/26 classification changed')
        selected={q['graph_output_chain'][-1]:q for q in read(plan['bpf_qualified_selection'])['objects']}
        need({q['output'] for q in self.matrix['rows']}==set(selected),'BPF matrix output selection changed')
        for classified in self.matrix['rows']:
            target=classified['output'];qualified=selected[target];bound=self.rows[target]
            need(classified['qualification_row']==qualified and classified['qualification_row_sha256']==hash_bytes(json.dumps(qualified,sort_keys=True,separators=(',',':')).encode()),'Exact sealed BPF qualification row changed')
            need(classified['kind']==bound['provenance_kind'] and classified['current_sha256']==bound['artifact']['sha256'],'BPF classification/map identity changed')
            if classified['kind']=='QUALIFIED_BASELINE_ARTIFACT':
                need(bound.get('qualified_sha256')==qualified['sha256'] and not bound['runtime_requalification_required'],'Unqualified output cannot use baseline classification')
            else:need(bound['runtime_requalification_required'] is True,'Changed/new BPF runtime requalification must remain conditional')
        expected=set(self.map['prior_output_allowlist'])|set(self.map['baseline_output_allowlist'])
        need(set(self.rows)==expected and len(self.map['prior_output_allowlist'])==38 and len(self.map['baseline_output_allowlist'])==23,'Unknown/unbound map output')
        need(self.map['r8_kit_seal']==R8_SEAL and sha(Path(plan['r8_kit'])/'inputs/kit-pins.json')==R8_SEAL,'Wrong r8 cohort')
        review=read(self.root/'inputs/method-review/relational-lineage.json')
        reviewed_commands=read(self.root/'inputs/method-review/frozen-exact-commands.json')['commands']
        for reviewed in review['rows']:
            bound=self.rows[reviewed['output']];evidence=bound['execution']
            need(all(bound['artifact'][key]==reviewed['artifact'][key] for key in ['sha256','bytes','mtime_ns']),'Independently reviewed artifact relation changed')
            need(bound['command_hash_hex']==reviewed['native_state']['cmd_hash_hex'] and evidence['metrics']==reviewed['frozen_metrics'] and evidence['ninja']['raw_v5_row']==reviewed['frozen_ninja']['text'],'Independently reviewed native relation changed')
            need(evidence['verbose']['command'] in [row['text'] for row in reviewed['frozen_commands']+reviewed_commands],'Independently reviewed exact command changed')
        self.prior=phases(Path(plan['r8_kit']),set(self.rows))
        need({Path(x['folder']).name:x['receipt_sha256'] for x in self.prior}==self.map['r8_phase_pins'],'R8 phase evidence pins changed')
        self.current=(phases(self.root,set(self.rows)) if (self.root/'attempt/native-evidence').exists() else []) if current_bundle is None else current_bundle
        self.state=selected_state(self.aosp,set(self.rows)) if state is None else state
        self.dependencies=selected_deps(self.aosp,set(self.rows)) if dependencies is None else dependencies
        self.graph_cache={};self.file_cache={};self.artifact_cache={};self.accepted={}
        reviewed_tools=read(self.root/'inputs/method-review/source-and-tools.json')
        for tool in ['prebuilts/siso/linux-x86/siso','prebuilts/clang/host/linux-x86/clang-r584948b/bin/clang++','prebuilts/rust-toolchain/linux-x86/1.93.1/bin/rustc']:
            current=self.pin(tool);expected=reviewed_tools[tool]
            need(current['sha256']==expected['sha256'] and current['bytes']==expected['bytes'],'Reviewed native engine/compiler tool changed: '+tool)
        prefix=self.catalog['global_prefix']
        with (self.aosp/prefix['path']).open('rb') as stream:data=stream.read(prefix['bytes'])
        need(hash_bytes(data)==prefix['sha256'],'Current compiler rule/global flags changed')
    def pin(self,relative):
        if relative not in self.file_cache:self.file_cache[relative]=file_pin(self.aosp/relative)
        return self.file_cache[relative]
    def context(self,row,current=False):
        edge=validate_context(self.aosp,row,self.catalog,self.graph_cache)
        need(row['module']==row['graph_context']['module'] and row['variant']==row['graph_context']['variant'],'Wrong native module/variant')
        for group in ['source_pins','toolchain_pins','response_pins']:
            for relative,pin in row[group].items():need(self.pin(relative)==pin,group+' changed: '+relative)
        if not current:
            for relative,pin in row['input_pins'].items():need(self.pin(relative)==pin,'Input changed; genuine new execution required: '+relative)
        for source in row['source_relations']:
            need(source in edge['inputs'] or row['graph_context']['kind']=='KATI_INSTALL' or source in row['module_sources'],'Wrong source/graph relation: '+source)
        dep=row['dependency_evidence']
        if not current and dep['kind']=='GCC_DEPSLOG':
            actual=self.dependencies.get(row['output']);need(actual is not None and actual==dep['record'],'Current compiler dependency relation changed')
        return edge
    def observed_artifact(self,target):
        if target not in self.artifact_cache:self.artifact_cache[target]=artifact(self.aosp/target)
        return self.artifact_cache[target]
    def base_output(self,target):
        need(target in self.rows,'Unknown unbound native output: '+target)
        row=self.rows[target];need(row['output']==target,'Wrong bound output path');node=self.state.get(target);actual=self.observed_artifact(target)
        if node is not None:
            need(node['digest'] is not None and node['digest']['hash']==actual['sha256'] and node['digest']['size_bytes']==actual['bytes'] and node['mtime_ns']==actual['mtime_ns'],'Native output digest/size/real metadata mismatch: '+target)
        return row,node,actual
    def record(self,target,source=None):
        row,node,actual=self.base_output(target)
        if source is not None:need(source in row['source_pins'] and source in row['source_relations'],'Wrong selected compiler source: '+source)
        current_candidates=[phase for phase in self.current if target in phase['metrics']]
        if current_candidates:
            phase=current_candidates[-1];need(phase['receipt']['exit_code']==0,'Current execution phase failed');need(node is not None,'Current execution lacks native output state')
            evidence=execution(phase,target,node['cmd_hash_hex'],self.aosp,row['rsp_candidates'])
            need(evidence is not None,'New execution/native command hash mismatch')
            need(node['cmd_hash_hex']==row['command_hash_hex'],'Current execution variant/flags changed')
            self.context(row,current=True)
            if row['provenance_kind']=='QUALIFIED_BASELINE_ARTIFACT':
                need(actual['sha256']==row['qualified_sha256'] and actual.get('elf_machine')==247,'Qualified digest changed; existing requalification required')
            dep=self.dependencies.get(target)
            if row['dependency_evidence']['kind']=='GCC_DEPSLOG':
                need(dep is not None and dep['mtime_ns']==actual['mtime_ns'],'Current execution compiler dependency record missing/stale')
                if source is not None:need(source in dep['dependencies'],'Current compiler source dependency missing')
            result=self.result(row,actual,node,'CURRENT_EXECUTION',evidence)
        elif row['provenance_kind']=='PRIOR_R8_EXECUTION':
            identity_keys=['name','mtime_ns','digest','cmd_hash_hex','edge_hash_hex','target']
            need(node is not None and all(node.get(k)==row['native_state'].get(k) for k in identity_keys),'Prior native record changed; new execution required')
            need(actual==row['artifact'],'Prior artifact identity changed');self.context(row)
            phase=next((p for p in self.prior if p['folder']==row['execution']['phase_path']),None);need(phase is not None,'Unknown prior phase')
            evidence=execution(phase,target,node['cmd_hash_hex'],self.aosp,row['rsp_candidates'])
            need(evidence==row['execution'],'Prior exact command/metric/Ninja/phase binding changed')
            need(phase['receipt']['exit_code']==row['execution']['phase_exit_code'],'Wrong prior phase result')
            if phase['receipt']['exit_code']:
                need(Path(phase['folder']).name=='bootimage' and phase['receipt']['exit_code']==1 and self.map['failed_r8_full_phase_is_product_success'] is False,'Unreviewed failed prior phase')
            result=self.result(row,actual,node,'PRIOR_R8_EXECUTION',evidence)
        else:
            need(row['provenance_kind']=='QUALIFIED_BASELINE_ARTIFACT' and target in self.map['baseline_output_allowlist'],'Unknown qualified baseline')
            need(actual['sha256']==row['qualified_sha256'] and actual.get('elf_machine')==247,'Qualified BPF digest/ELF changed; existing requalification required')
            identity_keys=['name','mtime_ns','digest','cmd_hash_hex','edge_hash_hex','target']
            need(actual==row['artifact'] and node is not None and all(node.get(k)==row['native_state'].get(k) for k in identity_keys),'Qualified baseline metadata changed');self.context(row)
            result=self.result(row,actual,node,'QUALIFIED_BASELINE_ARTIFACT',None)
        self.accepted[target]=result;return result
    @staticmethod
    def result(row,actual,node,kind,evidence):
        return dict(schema=SCHEMA,provenance_kind=kind,output=row['output'],sha256=actual['sha256'],bytes=actual['bytes'],real_mtime_ns=actual['mtime_ns'],native_state=node,prepared_native_state=row['native_state'],execution=evidence,module=row['module'],variant=row['variant'],source_pins=row['source_pins'],graph_context=row['graph_context'],commands=[evidence['verbose']['command']] if evidence else [],historical_all_input_bytes_attested=False,trust_model='controlled-tree/native-incremental',whole_product_success_from_prior_phase=False,runtime_requalification_required=row.get('runtime_requalification_required',False))
    def preflight(self):
        for target in self.rows:self.record(target)
        return dict(scope='EXPLICIT_PREPARATION_LINEAGE_ONLY',outputs=len(self.accepted),prior_r8=38,qualified_bpf_baseline=23,current_native_closure_established=False,launch_authorized=False,parent_method_sha256=METHOD_SHA)
    def final_closure(self):return require_current_closure(self.root,self.plan,self.current)

def require_ready(plan):return Session(Path(plan['run_root']),plan).preflight()
if __name__=='__main__':print(json.dumps(require_ready(read(Path(sys.argv[1])/'inputs/plan.json')),indent=2))
