"""Behavior regressions for copy/generation distinction and Ninja lexical binding."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from test_capture import Fixture,ROOT,TMP,PRODUCT
from graph import Graph
from ninja import evaluate
from provenance import AGGREGATE,aggregate_plan,bind_aggregate,install_kind,copy_source,digest
from safeio import Tree,Refusal

class SmallGraph:
    def __init__(self, directory, text, extras=None):
        self.root=Path(directory);(self.root/'out').mkdir()
        self.path=self.root/'out/main.ninja';self.path.write_text(text)
        for name,data in (extras or {}).items():(self.root/'out'/name).write_text(data)
        self.tree=Tree(self.root)
        limits=json.loads((ROOT/'inputs/profile-r8.json').read_bytes())['limits']
        limits.update(graph_file_bytes=1024**2,graph_total_bytes=4*1024**2,index_bytes=8*1024**2)
        self.graph=Graph(self.tree,['out/main.ninja']+['out/'+p for p in (extras or {})],self.root/'index.sqlite',limits)
    def close(self):self.graph.close();self.tree.close()

def aggregate_fixture(directory):
    target=AGGREGATE;parts=[];inputs=[];sources=[]
    rule='rule aggregate\n  command = /bin/bash -c "(rm -f '+target+' ) && (touch '+target+' )'
    for i in range(39):
        path='out/soong/.intermediates/apex/module%02d/apexkeys.txt'%i;source='out/soong/raw-lineage_p00a/data%02d'%i
        inputs.append(path);sources.append(source)
        parts.append('build '+path+': raw '+source+' | Cmp-deps Cp-deps\n')
        rule+=' && (cat '+path+' >> '+target+' )'
    rule+='"\n'
    text=rule+'rule raw\n  command = if ! prebuilts/build-tools/path/linux-x86/cmp -s $in $out; then prebuilts/build-tools/path/linux-x86/cp $in $out; fi\n'
    text+='build Cmp-deps: phony prebuilts/build-tools/path/linux-x86/cmp\nbuild Cp-deps: phony prebuilts/build-tools/path/linux-x86/cp\n'
    text+=''.join(parts)+'build '+target+': aggregate '+' '.join(inputs)+'\n'
    f=SmallGraph(directory,text);g=f.graph;e=g.edge(target)
    spec={'target':target,'edge_sha256':digest(e['raw']),'rule_sha256':digest(e['raw_rule']),'dependencies':copy.deepcopy(e['dependencies']),'input_producers':{},'generator_sources':[],'generator_tools':['prebuilts/build-tools/path/linux-x86/cmp','prebuilts/build-tools/path/linux-x86/cp']}
    for path,source in zip(inputs,sources):
        child=g.edge(path);spec['input_producers'][path]={'edge_sha256':digest(child['raw']),'rule_sha256':digest(child['raw_rule']),'dependencies':copy.deepcopy(child['dependencies']),'source':source}
    for name in ('build/make/core/Makefile','build/soong/apex/key.go','build/soong/android/raw_files.go'):
        p=f.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'public generator fixture\n');spec['generator_sources'].append({'path':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    class State:
        def __init__(self):self.trees={'aosp':f.tree};self.rows={};self.profile={'limits':{'file_bytes':1024**2}}
        def add(self,root,path,group,hash_only=False):
            row={'kind':'file',**f.tree.digest(path,1024**2)};self.rows[root+':'+path]=row;return row
    state=State();concat=b''
    for i,(path,source) in enumerate(zip(inputs,sources)):
        data=('module%02d public metadata\n'%i).encode();concat+=data
        for name in (path,source):p=f.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    for tool in spec['generator_tools']:p=f.root/tool;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'public fixture tool\n')
    p=f.root/target;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(concat);state.add('aosp',target,'selected')
    return f,state,{'schema':1,'ordinary_install_sources':{},'aggregate':spec},e

class ProducerTests(unittest.TestCase):
    def graph(self,text):
        tmp=tempfile.TemporaryDirectory(dir=TMP);self.addCleanup(tmp.cleanup)
        f=SmallGraph(tmp.name,text);self.addCleanup(f.close);return f.graph
    def test_normal_copy_exact_source(self):
        g=self.graph('rule cp\n  command = cp $in $out\nbuild out/a: cp src/right\n')
        self.assertEqual(copy_source(g.edge('out/a'),'src/right'),'src/right')
    def test_normal_copy_wrong_reviewed_source_refuses(self):
        g=self.graph('rule cp\n  command = cp $in $out\nbuild out/a: cp src/wrong\n')
        with self.assertRaisesRegex(Refusal,'INSTALL_SOURCE'):copy_source(g.edge('out/a'),'src/right')
    def test_normal_copy_command_wrong_source_refuses(self):
        g=self.graph('rule cp\n  command = cp src/wrong $out\nbuild out/a: cp src/right\n')
        with self.assertRaisesRegex(Refusal,'PRODUCER_COMMAND'):copy_source(g.edge('out/a'))
    def test_option_shaped_copy_source_refuses(self):
        g=self.graph('rule cp\n  command = cp $in $out\nbuild out/a: cp -unsafe/source\n')
        with self.assertRaisesRegex(Refusal,'PRODUCER_COMMAND'):copy_source(g.edge('out/a'))
    def test_normal_copy_multiple_inputs_refuses(self):
        g=self.graph('rule cp\n  command = cp $in $out\nbuild out/a: cp src/a src/b\n')
        with self.assertRaisesRegex(Refusal,'INSTALL_SOURCE'):copy_source(g.edge('out/a'))
    def test_unknown_metadata_name_does_not_grant_generation(self):
        g=self.graph('rule gen\n  command = arbitrary-generator $in $out\nbuild out/arbitrary/build.prop: gen src/a\n')
        with self.assertRaisesRegex(Refusal,'PRODUCER_COMMAND'):install_kind(g.edge('out/arbitrary/build.prop'),None)
    def test_copy_bytes_still_checked_by_capture(self):
        with tempfile.TemporaryDirectory(dir=TMP) as tmp:
            f=Fixture(tmp);f.put('aosp',f.source_paths['system/bin/init'],b'wrong bytes')
            with self.assertRaisesRegex(Refusal,'INSTALL_BYTES'):f.run()
    def aggregate(self):
        tmp=tempfile.TemporaryDirectory(dir=TMP);self.addCleanup(tmp.cleanup)
        f,state,contract,edge=aggregate_fixture(tmp.name);self.addCleanup(f.close);return f,state,contract,edge
    def test_genuine_39_input_aggregate_binds_all_sources_and_bytes(self):
        f,state,c,e=self.aggregate();plan=aggregate_plan(f.graph,e,c);bind_aggregate(state,e,plan)
        self.assertEqual(len(plan['inputs']),39);self.assertEqual(len(plan['input_producers']),39)
        self.assertTrue(all('aosp:'+x['source'] in state.rows for x in plan['input_producers']))
        self.assertEqual(install_kind(e,c)['kind'],'reviewed-aggregate')
    def test_aggregate_omitted_or_changed_dependency_refuses(self):
        f,state,c,e=self.aggregate()
        for mutate in ('omit','change','implicit'):
            x=copy.deepcopy(e)
            if mutate=='omit':x['dependencies'].pop()
            elif mutate=='change':x['dependencies'][0]['path']='out/other/apexkeys.txt'
            else:x['dependencies'][0]['kind']='implicit'
            with self.subTest(mutate=mutate),self.assertRaisesRegex(Refusal,'GENERATION_DEPENDENCIES'):aggregate_plan(f.graph,x,c)
    def test_aggregate_wrong_producer_and_command_refuse(self):
        f,state,c,e=self.aggregate()
        for field in ('raw','raw_rule','command'):
            x=copy.deepcopy(e);x[field]+=' changed'
            with self.subTest(field=field),self.assertRaisesRegex(Refusal,'GENERATION_PRODUCER|PRODUCER_COMMAND'):aggregate_plan(f.graph,x,c)
    def test_aggregate_omitted_generator_source_or_tool_refuses(self):
        f,state,c,e=self.aggregate()
        for field in ('generator_sources','generator_tools'):
            changed=copy.deepcopy(c);changed['aggregate'][field].pop()
            with self.subTest(field=field),self.assertRaisesRegex(Refusal,'GENERATION_SOURCE'):aggregate_plan(f.graph,e,changed)
    def test_aggregate_changed_generator_source_bytes_refuse(self):
        f,state,c,e=self.aggregate();plan=aggregate_plan(f.graph,e,c)
        (f.root/plan['generator_sources'][0]['path']).write_bytes(b'changed generator')
        with self.assertRaisesRegex(Refusal,'GENERATION_SOURCE'):bind_aggregate(state,e,plan)
    def test_aggregate_wrong_output_bytes_refuse(self):
        f,state,c,e=self.aggregate();plan=aggregate_plan(f.graph,e,c)
        (f.root/AGGREGATE).write_bytes(b'wrong aggregate');state.add('aosp',AGGREGATE,'selected')
        with self.assertRaisesRegex(Refusal,'GENERATION_BYTES'):bind_aggregate(state,e,plan)
    def test_aggregate_changed_raw_metadata_bytes_refuse(self):
        f,state,c,e=self.aggregate();plan=aggregate_plan(f.graph,e,c)
        (f.root/plan['input_producers'][0]['source']).write_bytes(b'changed raw input')
        with self.assertRaisesRegex(Refusal,'GENERATION_INPUT_BYTES'):bind_aggregate(state,e,plan)
    def test_aggregate_wrong_tool_alias_refuses(self):
        f,state,c,e=self.aggregate();f.graph.db.execute("UPDATE blocks SET text='build Cp-deps: phony prebuilts/wrong\\n' WHERE kind='edge' AND name='Cp-deps'")
        with self.assertRaisesRegex(Refusal,'GENERATION_TOOL'):aggregate_plan(f.graph,e,c)
    def test_private_install_source_and_signed_runtime_source_remain_refusals(self):
        g=self.graph('rule cp\n  command = cp $in $out\nbuild out/a: cp private/never-open.pk8\n')
        with self.assertRaisesRegex(Refusal,'EXCLUDED'):copy_source(g.edge('out/a'))
        contract=json.loads((ROOT/'inputs/provenance-contract.json').read_bytes())
        signed=PRODUCT+'system/apex/com.android.runtime.apex';edge={'output':signed,'outputs':[signed],'dependencies':[{'path':'src/wrong.apex','kind':'explicit'}],'command':'cp src/wrong.apex '+signed}
        with self.assertRaisesRegex(Refusal,'INSTALL_SOURCE'):install_kind(edge,contract)

    def test_capture_aggregate_branch_preserves_full_fixture_contract(self):
        from unittest.mock import patch
        import shutil
        import capture
        with tempfile.TemporaryDirectory(dir=TMP) as tmp, tempfile.TemporaryDirectory(dir=TMP) as agg_tmp:
            f=Fixture(tmp);af,state,contract,edge=aggregate_fixture(agg_tmp)
            try:
                graph_text=af.path.read_text()
                original=f.graph.read_text()
                original='\n'.join(line for line in original.splitlines() if not line.startswith('build '+AGGREGATE+':'))+'\n'
                f.graph.write_text(original+graph_text)
                for p in af.root.rglob('*'):
                    if p.is_file() and p!=af.path and p.name!='index.sqlite':
                        destination=f.root/'aosp'/p.relative_to(af.root);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,destination)
                base=capture.Selection
                class SyntheticSelection(base):
                    def __init__(self,*args,**kwargs):
                        super().__init__(*args,**kwargs);self.producer_contract=contract
                with patch.object(capture,'Selection',SyntheticSelection):result=f.run()
                self.assertEqual(result['status'],'COMPLETE')
                receipt=json.loads((f.output('select-1')/'selection.json').read_bytes())
                self.assertEqual(receipt['edges'][AGGREGATE]['producer_classification']['kind'],'reviewed-aggregate')
                self.assertEqual(len(receipt['edges'][AGGREGATE]['generation_provenance']['inputs']),39)
                self.assertFalse(receipt['runtime_ready']);self.assertFalse(receipt['physical_GO'])
            finally:af.close()
    def test_nondefault_profile_requires_exact_external_sha_for_plan(self):
        import subprocess,sys
        with tempfile.TemporaryDirectory(dir=TMP) as tmp:
            profile=Path(tmp)/'reviewed-fixture-profile.json';data=(ROOT/'inputs/profile-r8.json').read_bytes();profile.write_bytes(data)
            argv=[sys.executable,'-B',str(ROOT/'source/capture.py'),'plan','--profile',str(profile),'--profile-sha256']
            wrong=subprocess.run(argv+['0'*64],capture_output=True,text=True)
            self.assertNotEqual(wrong.returncode,0);self.assertIn('CONTRACT_PIN',wrong.stdout)
            right=subprocess.run(argv+[hashlib.sha256(data).hexdigest()],capture_output=True,text=True,check=True)
            plan=json.loads(right.stdout);self.assertFalse(plan['source_or_output_inspected']);self.assertFalse(plan['lock_acquired'])

class NinjaBindingTests(unittest.TestCase):
    def graph(self,text,extras=None):
        tmp=tempfile.TemporaryDirectory(dir=TMP);self.addCleanup(tmp.cleanup)
        f=SmallGraph(tmp.name,text,extras);self.addCleanup(f.close);return f.graph
    def test_undefined_optional_variable_is_empty(self):
        g=self.graph('rule cp\n  command = cp $cpFlags $in $out\nbuild out/a: cp src/a\n')
        e=g.edge('out/a');self.assertEqual(e['command'],'cp  src/a out/a');self.assertIn('cpFlags',e['undefined_or_empty_variables'])
    def test_defined_file_and_build_bindings_and_eager_values(self):
        g=self.graph('value = before\nsaved = $value\nrule cp\n  command = echo $saved $value $local\nbuild out/a: cp src/a\n  local = $value\nvalue = after\n')
        self.assertEqual(g.edge('out/a')['command'],'echo before after before')
    def test_escaped_dollars_are_not_expanded_twice(self):
        g=self.graph('literal = $$cpFlags\nrule cp\n  command = echo $$shell $literal $$(dirname $in)\nbuild out/a: cp src/a\n')
        self.assertEqual(g.edge('out/a')['command'],'echo $shell $cpFlags $(dirname src/a)')
    def test_subninja_shadow_does_not_leak_and_include_shares_scope(self):
        g=self.graph('v = root\nrule show\n  command = echo $v\nsubninja out/child.ninja\ninclude out/shared.ninja\nbuild out/root: show\n',{'child.ninja':'v = child\nbuild out/child: show\n','shared.ninja':'v = included\n'})
        self.assertEqual(g.edge('out/root')['command'],'echo included');self.assertEqual(g.edge('out/child')['command'],'echo child')
    def test_child_inherits_parent_late_bindings(self):
        g=self.graph('v = before\nrule show\n  command = echo $v\nsubninja out/child.ninja\nv = after\n',{'child.ninja':'build out/child: show\n'})
        self.assertEqual(g.edge('out/child')['command'],'echo after')
    def test_rule_scope_shadow_and_sibling_isolation(self):
        g=self.graph('rule show\n  command = echo parent\nsubninja out/a.ninja\nsubninja out/b.ninja\n',{'a.ninja':'rule show\n  command = echo a\nbuild out/a: show\n','b.ninja':'build out/b: show\n'})
        self.assertEqual(g.edge('out/a')['command'],'echo a');self.assertEqual(g.edge('out/b')['command'],'echo parent')
    def test_rule_binding_cycles_refuse(self):
        g=self.graph('rule show\n  command = $description\n  description = $command\nbuild out/a: show\n')
        with self.assertRaisesRegex(Refusal,'GRAPH_VARIABLE'):g.edge('out/a')
    def test_malformed_escapes_and_empty_dependency_refuse(self):
        with self.assertRaisesRegex(Refusal,'GRAPH_SYNTAX'):evaluate('echo $',lambda n:'')
        for command in ('echo ${missing','echo ${}','echo $?'):
            with self.subTest(command=command):
                g=self.graph('rule show\n  command = '+command+'\nbuild out/a: show\n')
                with self.assertRaisesRegex(Refusal,'GRAPH_SYNTAX'):g.edge('out/a')
        g=self.graph('rule show\n  command = echo $in\nbuild out/a: show $missing\n')
        with self.assertRaisesRegex(Refusal,'GRAPH_SYNTAX'):g.edge('out/a')
    def test_unbraced_dot_and_braced_dot_follow_lexer(self):
        g=self.graph('a = simple\na.dot = braced\nrule show\n  command = echo $a.dot ${a.dot}\nbuild out/a: show\n')
        self.assertEqual(g.edge('out/a')['command'],'echo simple.dot braced')
    def test_edge_bindings_do_not_see_other_edge_bindings(self):
        g=self.graph('x = file\nrule show\n  command = echo $x $y\nbuild out/a: show\n  x = edge\n  y = $x\n')
        self.assertEqual(g.edge('out/a')['command'],'echo edge file')
    def test_unknown_rule_and_include_cycles_refuse(self):
        g=self.graph('build out/a: missing\n')
        with self.assertRaisesRegex(Refusal,'GRAPH_UNKNOWN'):g.edge('out/a')
        with self.assertRaisesRegex(Refusal,'GRAPH_INCLUDE'):self.graph('subninja out/a.ninja\n',{'a.ninja':'subninja out/main.ninja\n'})

    def test_escaped_trailing_space_survives_value_parsing(self):
        g=self.graph('rule show\n  command = echo tail$ \nbuild out/a: show\n')
        self.assertEqual(g.edge('out/a')['command'],'echo tail ')
    def test_unknown_rule_binding_refuses(self):
        g=self.graph('rule show\n  command = echo ok\n  misspelled = unsafe\nbuild out/a: show\n')
        with self.assertRaisesRegex(Refusal,'GRAPH_RULE'):g.edge('out/a')
    def test_builtin_paths_use_ninja_posix_shell_quoting(self):
        g=self.graph('rule show\n  command = echo $in $out\nbuild out/a@b: show src/a@b\n')
        self.assertEqual(g.edge('out/a@b')['command'],"echo 'src/a@b' 'out/a@b'")
    def test_eager_self_shadow_uses_previous_value_not_a_cycle(self):
        g=self.graph('v = first\nv = $v second\nrule show\n  command = echo $v\nbuild out/a: show\n')
        self.assertEqual(g.edge('out/a')['command'],'echo first second')

    def test_escaped_dollar_at_end_of_rule_line_does_not_swallow_build(self):
        g=self.graph('rule show\n  command = echo $$\nbuild out/a: show\n')
        self.assertEqual(g.edge('out/a')['command'],'echo $')

    def test_empty_child_binding_shadows_nonempty_parent(self):
        g=self.graph('v = parent\nrule show\n  command = echo [$v]\nsubninja out/child.ninja\n',{'child.ninja':'v =\nbuild out/child: show\n'})
        self.assertEqual(g.edge('out/child')['command'],'echo []')
    def test_file_binding_without_spaces_around_equals(self):
        g=self.graph('v=value\nrule show\n  command = echo $v\nbuild out/a: show\n')
        self.assertEqual(g.edge('out/a')['command'],'echo value')
