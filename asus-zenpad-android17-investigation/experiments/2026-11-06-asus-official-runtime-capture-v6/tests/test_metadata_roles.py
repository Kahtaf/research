"""Small synthetic source-role/authentication tests; no native tool/product access."""
import copy,hashlib,json,struct,tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from test_capture import ROOT,TMP,Fixture
from safeio import Tree,Refusal,sha
import metadata_roles as m

class MetadataFixture:
    def __init__(self,root):
        self.root=Path(root);self.aosp=self.root/'aosp';self.kit=self.root/'kit';self.aosp.mkdir();self.kit.mkdir()
        self.profile={'revision':'r8','aosp':str(self.aosp),'product_out':str(self.aosp/'out/target/product/p00a')}
        self.selector=json.loads((ROOT/'inputs/selector.json').read_bytes());self.binding={'revision':'r8'};self.rows={}
        self.write('kit','attempt/validation/source-postimages.json',b'{"fixture_only":true}\n')
        self.source_sha=sha((self.kit/'attempt/validation/source-postimages.json').read_bytes())
        files=[]
        for i,path in enumerate(m.FOUR):
            data=('public installed fixture %d\n'%i).encode();relative='out/target/product/p00a'+path;self.write('aosp',relative,data);files.append({'path':path,'sha256':sha(data),'bytes':len(data)})
        receipt={'schema':m.RECEIPT_SCHEMA,'build_id':'r8','source_binding_sha256':self.source_sha,'files':files}
        self.plan={'schema':m.PLAN_SCHEMA,'build_id':'r8','source_binding_sha256':self.source_sha,'tool_group_sha256':m.GROUP,'native_target_out':self.profile['product_out']+'/system/','search_root':self.profile['product_out'],'search_slots':[],'contexts':{'format':'compiled','origin':self.profile['product_out']+'/obj/ETC/final/file_contexts.bin','sha256':sha(bytes.fromhex('8aff7cf9')+b'synthetic-not-native-compiled')},'installed_content_receipt':receipt}
        for slot in m.SLOTS:
            origin=self.profile['product_out']+'/'+slot+'/etc/fs_config_files'
            if slot=='system':self.write('aosp',self.relative(origin),b'');row={'slot':slot,'state':'present','origin':origin,'sha256':sha(b''),'absence_attestation_sha256':None}
            else:row={'slot':slot,'state':'absent','origin':origin,'sha256':None,'absence_attestation_sha256':sha(m.encoded({'build_id':'r8','source_binding_sha256':self.source_sha,'slot':slot,'origin':origin,'state':'absent'}))}
            self.plan['search_slots'].append(row)
        self.write('aosp',self.relative(self.plan['contexts']['origin']),bytes.fromhex('8aff7cf9')+b'synthetic-not-native-compiled')
        self.trees={'aosp':Tree(self.aosp),'kit':Tree(self.kit)};self.refresh()
    def relative(self,path):return path[len(self.profile['aosp'])+1:]
    def write(self,root,path,data):
        p=(self.aosp if root=='aosp' else self.kit)/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    def refresh(self):
        raw=(json.dumps(self.plan,indent=2)+'\n').encode();self.write('kit',m.PLAN,raw);self.profile['host_metadata_source_plan_sha256']=sha(raw)
        validation={'fixture_only':True,'host_metadata_source_plan_sha256':sha(raw),'installed_four_content_receipt_sha256':sha(m.encoded(self.plan['installed_content_receipt']))}
        self.write('kit','attempt/validation/complete.json',(json.dumps(validation)+'\n').encode())
        for name in ('attempt/validation/source-postimages.json','attempt/validation/complete.json'):self.add('kit',name,'fixture')
    def add(self,root,path,group,hash_only=False,allow_empty=False):
        row={'kind':'file',**self.trees[root].digest(path,4*1024**2,allow_empty=allow_empty)};self.rows[root+':'+path]=row;return row
    def close(self):
        for t in self.trees.values():t.close()

class MetadataRoleTests(unittest.TestCase):
    def fixture(self):
        tmp=tempfile.TemporaryDirectory(dir=TMP);self.addCleanup(tmp.cleanup);f=MetadataFixture(tmp.name);self.addCleanup(f.close);return f
    def test_explicit_present_empty_and_absent_slots_stay_distinct(self):
        f=self.fixture();calls=[];roles=m.collect(f,ROOT,host_exists=lambda p:(calls.append(p) or False))
        self.assertEqual(roles['search_slots'][0]['state'],'present');self.assertEqual(roles['search_slots'][0]['bytes'],0)
        self.assertEqual(roles['search_slots'][0]['record_count'],0);self.assertIsNone(roles['search_slots'][1]['sha256'])
        self.assertEqual(set(calls),{'/'+x+'/etc/fs_config_files' for x in m.SLOTS[1:]})
        self.assertFalse(roles['native_query_executed']);self.assertFalse(roles['production_admission']);self.assertFalse(roles['query_layout_materialized'])
    def test_native_root_spelling_normalizes_once_and_wrong_root_refuses(self):
        f=self.fixture();root=f.profile['product_out']
        for value in (root,root+'/',root+'/system',root+'/system/'):self.assertEqual(m.normalize_native(value),root)
        for field in ('native_target_out','search_root'):
            bad=copy.deepcopy(f.plan);bad[field]='/arbitrary/root'
            with self.subTest(field=field),self.assertRaisesRegex(Refusal,'METADATA_ROOT'):m.validate_plan(bad,f.profile,f.source_sha)
    def test_all_six_slots_and_exact_schema_required(self):
        f=self.fixture()
        for mutate in ('omit','order','unknown','dirs','exit0'):
            p=copy.deepcopy(f.plan)
            if mutate=='omit':p['search_slots'].pop()
            elif mutate=='order':p['search_slots'].reverse()
            elif mutate=='unknown':p['search_slots'][0]['optional']=True
            elif mutate=='dirs':p['search_slots'][0]['origin']=p['search_slots'][0]['origin'].replace('fs_config_files','fs_config_dirs')
            else:p['resolver_exit']=0
            with self.subTest(mutate=mutate),self.assertRaises(Refusal):m.validate_plan(p,f.profile,f.source_sha)
    def test_missing_present_override_refuses_instead_of_fallback(self):
        f=self.fixture();(f.aosp/f.relative(f.plan['search_slots'][0]['origin'])).unlink()
        with self.assertRaises(FileNotFoundError):m.collect(f,ROOT,host_exists=lambda p:False)
    def test_malformed_override_refuses_even_under_rebound_declared_hash(self):
        f=self.fixture();row=f.plan['search_slots'][0];data=bytes(16);f.write('aosp',f.relative(row['origin']),data);row['sha256']=sha(data);f.refresh()
        with self.assertRaisesRegex(Refusal,'METADATA_OVERRIDE'):m.collect(f,ROOT,host_exists=lambda p:False)
    def test_declared_absence_cannot_be_synthesized_empty(self):
        f=self.fixture();row=f.plan['search_slots'][1];f.write('aosp',f.relative(row['origin']),b'')
        with self.assertRaisesRegex(Refusal,'METADATA_ABSENCE'):m.collect(f,ROOT,host_exists=lambda p:False)
    def test_absolute_host_fallback_presence_refuses_and_is_rechecked(self):
        f=self.fixture()
        with self.assertRaisesRegex(Refusal,'METADATA_HOST_FALLBACK'):m.collect(f,ROOT,host_exists=lambda p:p=='/vendor/etc/fs_config_files')
        roles=m.collect(f,ROOT,host_exists=lambda p:False)
        with self.assertRaisesRegex(Refusal,'METADATA_HOST_FALLBACK'):m.recheck(f,roles,host_exists=lambda p:p=='/vendor/etc/fs_config_files')
    def test_only_final_compiled_contexts_no_alternate_fields(self):
        f=self.fixture()
        for mutate in ('text','sidecar','wrong-origin'):
            p=copy.deepcopy(f.plan)
            if mutate=='text':p['contexts']['format']='text'
            elif mutate=='sidecar':p['contexts']['alternate']='file_contexts'
            else:p['contexts']['origin']='/tmp/file_contexts.bin'
            with self.subTest(mutate=mutate),self.assertRaises(Refusal):m.validate_plan(p,f.profile,f.source_sha)
    def test_corrupt_compiled_header_refuses_without_native_query(self):
        f=self.fixture();data=b'not-compiled';f.write('aosp',f.relative(f.plan['contexts']['origin']),data);f.plan['contexts']['sha256']=sha(data);f.refresh()
        with self.assertRaisesRegex(Refusal,'METADATA_CONTEXTS'):m.collect(f,ROOT,host_exists=lambda p:False)
    def test_complete_source_content_and_tool_bindings_are_authenticated(self):
        for mutate in ('complete','source','content','group'):
            f=self.fixture()
            if mutate=='complete':f.profile['host_metadata_source_plan_sha256']='0'*64
            elif mutate=='source':f.plan['source_binding_sha256']='0'*64;f.refresh()
            elif mutate=='content':f.write('aosp','out/target/product/p00a'+m.FOUR[2],b'changed installed bytes')
            else:f.plan['tool_group_sha256']='0'*64;f.refresh()
            with self.subTest(mutate=mutate),self.assertRaises(Refusal):m.collect(f,ROOT,host_exists=lambda p:False)
    def test_only_fixed_four_and_independent_content_receipt(self):
        f=self.fixture();f.plan['installed_content_receipt']['files'][2]['path']='/system/bin/arbitrary';f.refresh()
        with self.assertRaisesRegex(Refusal,'METADATA_CONTENT'):m.collect(f,ROOT,host_exists=lambda p:False)
    def test_accepted_tools_remain_external_tool_scope_only(self):
        selector=json.loads((ROOT/'inputs/selector.json').read_bytes());ref=m.reference(ROOT,selector['host_metadata_reference_sha256'])
        self.assertEqual(ref['tool_group_sha256'],m.GROUP);self.assertFalse(ref['dependency_bytes_revalidated_here']);self.assertTrue(ref['guarded_query_revalidation_required'])
    def test_real_capture_cannot_omit_source_role_plan(self):
        from capture import Selection
        state=SimpleNamespace(profile={'aosp':'/srv/android/lineage24'})
        with self.assertRaisesRegex(Refusal,'METADATA_SOURCE_ROLES_REQUIRED'):Selection.capture_host_metadata(state)
    def test_empty_file_exception_cannot_escape_fixed_slot_role(self):
        from capture import Selection
        with tempfile.TemporaryDirectory(dir=TMP) as tmp:
            f=Fixture(tmp);state=Selection(f.profile,f.selector,Path(tmp)/'snapshots')
            try:
                with self.assertRaisesRegex(Refusal,'METADATA_EMPTY'):state.add('aosp','src/public.txt','ordinary',allow_empty=True)
            finally:state.close()
