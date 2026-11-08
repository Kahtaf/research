"""Behavioral fixtures for the controlled incremental admission boundary."""
import base64,copy,hashlib,os,sys,tempfile,unittest,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from cache_lineage import Session,file_pin
from native_state import artifact
from graph_context import hash_bytes
from frozen_channel import execution,native_hash

class LineageTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='lineage-',dir='/srv/android/asus-reviewed-build-kit/r9-exec-r1-fixtures');self.r=Path(self.tmp.name)
  self.target='out/soong/.intermediates/example/demo/android_arm64_armv8-a/obj/demo.o'
  self.source='example/demo.c';self.rsp=self.target+'.rsp'
  for rel,data in [(self.target,b'actual-output'),(self.source,b'int demo;'),(self.rsp,b'-DDEMO=1'),('compiler',b'compiler')]:
   p=self.r/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  os.utime(self.r/self.target,ns=(1577836800000000000,1577836800000000000))
  text='# Module:  demo\n# Variant: android_arm64_armv8-a\n# Defined: example/Android.bp:1:1\nbuild '+self.target+': cc '+self.source+'\n  flags = -DDEMO=1\n'
  (self.r/'graph').write_text(text)
  block=dict(path='graph',offset=0,bytes=len(text),sha256=hash_bytes(text.encode()),text=text)
  edge=text[text.index('build '):]
  self.command='clang -c '+self.source+' -o '+self.target
  ch=native_hash(self.command,(self.r/self.rsp).read_bytes());actual=artifact(self.r/self.target)
  self.node=dict(digest=dict(hash=actual['sha256'],size_bytes=actual['bytes']),mtime_ns=actual['mtime_ns'],cmd_hash_hex=ch,updated_time_ns=1577836800000000000)
  self.phase=dict(folder=str(self.r/'prior/bootimage'),receipt_sha256='receipt',receipt=dict(exit_code=1,attempt_started_sha256='start',integration_sha256='integration'),commands={self.target:[dict(command=self.command,line=8,sha256=hash_bytes(self.command.encode()))]},metrics={self.target:[dict(line=10,value=dict(output=self.target,action_start=1,action_end=2,cmdhash=base64.b64encode(bytes.fromhex(ch)).decode()))]},ninja={self.target:dict(line=2,raw_v5_row='0\t1\t1\t'+self.target+'\t123')})
  self.row=dict(output=self.target,module='demo',variant='android_arm64_armv8-a',provenance_kind='PRIOR_R8_EXECUTION',artifact=actual,native_state=self.node,command_hash_hex=ch,graph_context=dict(kind='SOONG_MODULE',module='demo',variant='android_arm64_armv8-a',variant_sha256=hash_bytes(text.encode()),edge_sha256=hash_bytes(edge.encode())),module_sources=[self.source],source_relations=[self.source],source_pins={self.source:file_pin(self.r/self.source)},response_pins={self.rsp:file_pin(self.r/self.rsp)},toolchain_pins={'compiler':file_pin(self.r/'compiler')},input_pins={},dependency_evidence=dict(kind='GRAPH_AND_RSP'),rsp_candidates=[self.rsp])
  self.row['execution']=execution(self.phase,self.target,ch,self.r,[self.rsp])
  self.s=Session.__new__(Session);self.s.aosp=self.r;self.s.rows={self.target:self.row};self.s.prior=[self.phase];self.s.current=[];self.s.state={self.target:self.node};self.s.dependencies={};self.s.catalog=dict(modules={'demo':block});self.s.graph_cache={};self.s.file_cache={};self.s.artifact_cache={};self.s.accepted={};self.s.map=dict(failed_r8_full_phase_is_product_success=False,baseline_output_allowlist=[])
 def tearDown(self):self.tmp.cleanup()
 def admit(self):return self.s.record(self.target,self.source)
 def test_prior_absent_current_log_and_old_real_time_accepted(self):
  self.assertFalse((self.r/'out/.ninja_log').exists());r=self.admit();self.assertEqual(r['provenance_kind'],'PRIOR_R8_EXECUTION');self.assertEqual(r['real_mtime_ns'],1577836800000000000);self.assertFalse(r['historical_all_input_bytes_attested'])
 def test_wrong_digest_refused(self):
  (self.r/self.target).write_bytes(b'changed');self.assertRefused('digest')
 def test_wrong_command_hash_refused(self):
  self.s.state=copy.deepcopy(self.s.state);self.s.state[self.target]['cmd_hash_hex']='0'*64;self.assertRefused('Prior native record')
 def test_phase_action_error_refused(self):
  self.phase['metrics'][self.target][0]['value']['err']='failed';self.assertRefused('Failed native action')
 def test_wrong_output_path_refused(self):
  with self.assertRaisesRegex(ValueError,'Unknown unbound'):self.s.record(self.target+'-unknown')
 def test_wrong_source_pin_refused(self):
  (self.r/self.source).write_text('changed');self.assertRefused('source_pins')
 def test_wrong_response_bytes_refused(self):
  (self.r/self.rsp).write_text('changed');self.assertRefused('response_pins')
 def test_wrong_current_graph_refused(self):
  (self.r/'graph').write_text('changed');self.assertRefused('graph|module')
 def test_wrong_module_refused(self):
  self.row['module']='wrong';self.assertRefused('module/variant')
 def test_wrong_variant_refused(self):
  self.row['variant']='android_arm';self.assertRefused('module/variant')
 def test_wrong_selected_source_refused(self):
  with self.assertRaisesRegex(ValueError,'Wrong selected compiler source'):self.s.record(self.target,'another.c')
 def test_real_current_record_preferred_over_prior(self):
  phase=copy.deepcopy(self.phase);phase['folder']=str(self.r/'current/host_init_verifier');phase['receipt']['exit_code']=0;phase['receipt']['attempt_started_sha256']='new-start';self.s.current=[phase]
  r=self.admit();self.assertEqual(r['provenance_kind'],'CURRENT_EXECUTION');self.assertEqual(r['execution']['attempt_started_sha256'],'new-start')
 def test_current_failed_action_cannot_fall_back(self):
  phase=copy.deepcopy(self.phase);phase['receipt']['exit_code']=0;phase['metrics'][self.target][0]['value']['err']='failed';self.s.current=[phase];self.assertRefused('Failed native action')
 def test_current_wrong_command_cannot_fall_back(self):
  phase=copy.deepcopy(self.phase);phase['receipt']['exit_code']=0;phase['metrics'][self.target][0]['value']['cmdhash']=base64.b64encode(b'0'*32).decode();self.s.current=[phase];self.assertRefused('command hash')
 def test_failed_full_phase_individual_success_not_product_success(self):
  r=self.admit();self.assertEqual(r['execution']['phase_exit_code'],1);self.assertFalse(r['whole_product_success_from_prior_phase'])
 def test_unknown_qualified_baseline_refused(self):
  self.row['provenance_kind']='QUALIFIED_BASELINE_ARTIFACT';self.assertRefused('Unknown qualified baseline')
 def test_failed_or_pending_completed_command_refused(self):
  self.phase['commands'][self.target]=[];self.assertRefused('completed command')
 def test_frozen_ninja_corroboration_required(self):
  self.phase['ninja']={};self.assertRefused('frozen Ninja')
 def baseline(self):
  data=bytearray(64);data[:6]=b'\x7fELF\x02\x01';struct.pack_into('<H',data,18,247);(self.r/self.target).write_bytes(data)
  actual=artifact(self.r/self.target);self.row['artifact']=actual;self.node.update(digest=dict(hash=actual['sha256'],size_bytes=actual['bytes']),mtime_ns=actual['mtime_ns'])
  self.row['provenance_kind']='QUALIFIED_BASELINE_ARTIFACT';self.row['qualified_sha256']=actual['sha256'];self.s.map['baseline_output_allowlist']=[self.target]
 def test_exact_qualified_baseline_has_no_execution_claim(self):
  self.baseline();r=self.admit();self.assertEqual(r['provenance_kind'],'QUALIFIED_BASELINE_ARTIFACT');self.assertIsNone(r['execution']);self.assertEqual(r['commands'],[])
 def test_changed_qualified_digest_cannot_be_fresh_compile_shortcut(self):
  self.baseline();self.row['qualified_sha256']='f'*64;phase=copy.deepcopy(self.phase);phase['receipt']['exit_code']=0;self.s.current=[phase];self.assertRefused('Qualified digest changed')
 def test_wrong_baseline_elf_machine_refused(self):
  self.baseline();self.row['qualified_sha256']='f'*64;self.assertRefused('Qualified BPF digest/ELF')
 def test_native_bookkeeping_time_is_not_new_execution(self):
  self.s.state=copy.deepcopy(self.s.state);self.s.state[self.target]['updated_time_ns']+=100
  r=self.admit();self.assertEqual(r['provenance_kind'],'PRIOR_R8_EXECUTION');self.assertEqual(r['execution']['metrics']['value']['action_start'],1)
 def closure(self,host=True,full=True,failed=False,old=False):
  from frozen_channel import require_current_closure
  p=self.r/'attempt/started.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(dict(utc='2026-11-07T01:00:00+00:00')))
  m=self.r/'map';m.write_text(json.dumps(dict(records={})));plan=dict(native_lineage_map=str(m));bundle=[]
  for name,targets in [('host_init_verifier',['host_init_verifier']+(['bpfloader','vold'] if host else [])),('bootimage',['bootimage','systemimage'] if full else ['bootimage'])]:
   bundle.append(dict(folder=str(self.r/name),receipt_sha256='receipt',receipt=dict(exit_code=1 if failed else 0),metadata=dict(start_time='2026-11-07T00:00:00Z' if old else '2026-11-07T01:01:00Z',targets=targets)))
  return require_current_closure(self.r,plan,bundle)
 def test_current_native_closure_requires_explicit_platform_targets(self):
  with self.assertRaisesRegex(ValueError,'bpfloader/vold'):self.closure(host=False)
 def test_current_native_closure_requires_full_targets(self):
  with self.assertRaisesRegex(ValueError,'bootimage/systemimage'):self.closure(full=False)
 def test_current_native_closure_rejects_failed_or_old_phase(self):
  for flags in [dict(failed=True),dict(old=True)]:
   with self.assertRaises(ValueError):self.closure(**flags)
 def test_current_native_closure_positive_is_host_only(self):
  r=self.closure();self.assertEqual(r['scope'],'FINAL_CURRENT_ACCEPTANCE_NATIVE_CLOSURE');self.assertFalse(r['historical_all_input_bytes_attested'])
 def assertRefused(self,message):
  with self.assertRaisesRegex(ValueError,message):self.admit()

if __name__=='__main__':unittest.main()
