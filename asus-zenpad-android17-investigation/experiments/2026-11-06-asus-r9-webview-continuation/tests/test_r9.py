"""Linux behavior fixtures only; these do not qualify native product execution."""
import copy,gzip,hashlib,json,os,shutil,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import artifact as a
import integrate as i
import continuation as c
import cache_lineage as cl
from compiler_channel import commands_for
from verify_product_r3 import log_entries

def put(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data.encode() if isinstance(data,str) else data);return p

def js(p,d):return put(p,json.dumps(d))

class R9Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='r9-test-',dir='/srv/android/asus-reviewed-build-kit/r9-fixtures');self.r=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def test_exact_artifact(self):
  self.assertEqual(a.admit('/srv/android/asus-product-integration-staging/r9/webview.apk'),dict(sha256=a.OID,bytes=a.SIZE))
 def test_pointer_cannot_be_apk(self):
  p=put(self.r/'pointer',a.POINTER)
  with self.assertRaisesRegex(ValueError,'size mismatch'):a.admit(p)
 def test_wrong_size(self):
  with self.assertRaisesRegex(ValueError,'size mismatch'):a.admit(put(self.r/'short',b'PK'))
 def test_wrong_sha(self):
  p=put(self.r/'bad',b'abcd')
  with self.assertRaisesRegex(ValueError,'SHA256 mismatch'):a.admit(p,expected_size=4)
 def test_hash_matching_invalid_zip(self):
  p=put(self.r/'notzip',b'abcd')
  with self.assertRaises(zipfile.BadZipFile):a.admit(p,a.digest(p),4)
 def test_manifest_required(self):
  p=self.r/'zip'
  with zipfile.ZipFile(p,'w') as z:z.writestr('other',b'data')
  with self.assertRaisesRegex(ValueError,'Missing actual Android manifest'):a.admit(p,a.digest(p),p.stat().st_size)
 def test_symlink_rejected(self):
  p=self.r/'link';p.symlink_to('/srv/android/asus-product-integration-staging/r9/webview.apk')
  with self.assertRaisesRegex(ValueError,'regular file'):a.admit(p)
 def test_atomic_copy_preserves_pointer_and_refuses_repeat(self):
  dst=put(self.r/'source/webview.apk',a.POINTER);backup=self.r/'backup/pointer'
  unrelated=put(self.r/'unrelated','retained');inode=unrelated.stat().st_ino
  a.materialize('/srv/android/asus-product-integration-staging/r9/webview.apk',dst,backup)
  self.assertEqual(a.digest(dst),a.OID);self.assertEqual(backup.read_bytes(),a.POINTER)
  self.assertEqual(unrelated.stat().st_ino,inode);self.assertEqual(unrelated.read_text(),'retained')
  with self.assertRaisesRegex(ValueError,'preimage changed'):a.materialize(dst,dst,self.r/'backup2')
 def test_existing_backup_is_never_overwritten(self):
  dst=put(self.r/'source',a.POINTER);backup=put(self.r/'backup','sentinel')
  with self.assertRaises(FileExistsError):a.materialize('/srv/android/asus-product-integration-staging/r9/webview.apk',dst,backup)
  self.assertEqual(dst.read_bytes(),a.POINTER);self.assertEqual(backup.read_text(),'sentinel')
 def test_unreviewed_preimage_cannot_be_materialized(self):
  dst=put(self.r/'source',b'other')
  with self.assertRaisesRegex(ValueError,'preimage changed'):a.materialize('/srv/android/asus-product-integration-staging/r9/webview.apk',dst,self.r/'backup')
  self.assertFalse((self.r/'backup').exists())
 def test_existing_atomic_temp_is_preserved(self):
  dst=put(self.r/'source',a.POINTER);temp=put(self.r/'source.reviewed-r9-tmp','sentinel')
  with self.assertRaises(FileExistsError):a.materialize('/srv/android/asus-product-integration-staging/r9/webview.apk',dst,self.r/'backup')
  self.assertEqual(dst.read_bytes(),a.POINTER);self.assertEqual(temp.read_text(),'sentinel')
 def test_only_exact_selected_artifact_source_scope(self):
  d={a.REL:dict(before_sha256=a.BEFORE,before_bytes=134,after_sha256=a.OID,after_bytes=a.SIZE)};p=dict(r9_delta=str(js(self.r/'delta',d)))
  self.assertEqual(c.deltas(p),d)
  d['unrelated/source']=dict(before_sha256='0'*64);js(p['r9_delta'],d)
  with self.assertRaisesRegex(i.Refusal,'source scope changed'):c.deltas(p)
 def test_block_before_process_lock_source_or_attempt(self):
  for active in [False,True]:
   with self.assertRaisesRegex(ValueError,'CACHE_LINEAGE_INCOMPLETE'):i.execute({},self.r,active)
  self.assertEqual(list(self.r.iterdir()),[])
 def test_revision_reuse(self):
  logs=self.r/'logs';logs.mkdir();p=dict(revision='r9',logs=str(logs),run_root=str(self.r))
  i.revision_unused(p);put(logs/'full-build-r9.started','consumed')
  with self.assertRaisesRegex(i.Refusal,'Revision already used'):i.revision_unused(p)
 def test_prior_attempt_blocks_new_attempt(self):
  (self.r/'attempt').mkdir();logs=self.r/'logs';logs.mkdir()
  with self.assertRaisesRegex(i.Refusal,'Previous attempt exists'):i.revision_unused(dict(revision='r9',logs=str(logs),run_root=str(self.r)))
 def channel(self):
  q=self.r/'attempt';js(q/'started.json',{});js(q/'integration.json',{});f=q/'native-evidence/phase';f.mkdir(parents=True)
  with gzip.open(f/'verbose.log.gz','wt') as z:z.write('verbose: ninja: [1/3] clang -o pending x.c\n[1/3] clang -c -o good x.c\n[2/3] clang -o bad y.c\nFAILED: bad\n[3/3] clang++ -o link good\n')
  put(f/'.ninja_log','# ninja log v5\n0\t1\t100\tgood\ta1\n0\t1\t100\tlink\tb2\n')
  js(f/'receipt.json',dict(attempt_started_sha256=i.sha(q/'started.json'),integration_sha256=i.sha(q/'integration.json'),files={n:dict(sha256=i.sha(f/n),bytes=(f/n).stat().st_size) for n in ['verbose.log.gz','.ninja_log']}))
  return f
 def test_pending_failed_and_dependency_mentions_are_rejected(self):
  self.channel();cmds,_=commands_for(self.r,{'pending','good','bad','link'})
  self.assertEqual(set(cmds),{'good','link'});self.assertEqual(cmds['good'],['clang -c -o good x.c'])
 def test_current_ninja_identity_drift(self):
  f=self.channel();e=log_entries(f/'.ninja_log',{'good'});self.assertIn('good',commands_for(self.r,{'good'},e)[0]);e['good']['command_hash']='b2'
  self.assertEqual(commands_for(self.r,{'good'},e)[0],{})
 def test_missing_current_ninja_entry(self):
  self.channel();self.assertEqual(commands_for(self.r,{'good'},{} )[0],{})
 def test_native_attempt_binding_drift(self):
  self.channel();js(self.r/'attempt/started.json',dict(other=True))
  with self.assertRaisesRegex(i.Refusal,'attempt binding'):commands_for(self.r,{'good'})
 def test_frozen_command_tamper(self):
  f=self.channel();put(f/'verbose.log.gz','tampered')
  with self.assertRaisesRegex(i.Refusal,'evidence changed'):commands_for(self.r,{'good'})
 def test_missing_execution_dependency_receipt(self):
  with self.assertRaisesRegex(ValueError,'dependency closure'):cl.check_record({}, {})
 def test_each_inherited_identity_change_is_rejected(self):
  b={k:'bound-test-value' for k in ['attempt_started_sha256','integration_sha256','native_receipt_sha256','command','ninja','output_sha256','source_sha256','graph_sha256','toolchain_sha256','dependencies_sha256','build_id']};b['dependency_closure_complete']=True
  o=dict(b,completed=True,failed_action=False)
  for key in b.keys()-{'dependency_closure_complete'}:
   changed=dict(o);changed[key]='changed'
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,'identity changed'):cl.check_record(changed,b)
  for flags in [dict(completed=False),dict(failed_action=True)]:
   with self.assertRaisesRegex(ValueError,'Failed or pending'):cl.check_record(dict(o,**flags),b)
 def test_actual_terminal_requires_parent_acceptance(self):
  p=i.read(ROOT/'inputs/plan.json');d=c.terminal(p,describe=True)
  self.assertFalse(d['review_template']['reviewed_by_parent'])
  with self.assertRaisesRegex(i.Refusal,'Parent-authored'):c.terminal(p)
 def test_preservation_extra_attempt_file_rejected(self):
  logs=self.r/'logs';logs.mkdir();prior=self.r/'r8';put(prior/'attempt/extra','unexpected')
  p=dict(r8_kit=str(prior),r8_preservation=str(js(self.r/'pins',dict(attempt_files={},logs={}))),logs=str(logs))
  with self.assertRaisesRegex(i.Refusal,'attempt set drift'):c.preservation(p)
 def test_preservation_changed_log_rejected(self):
  logs=self.r/'logs';logs.mkdir();prior=self.r/'r8';(prior/'attempt').mkdir(parents=True);p=put(logs/'full-build-r8.log','first')
  pins=dict(attempt_files={},logs={str(p):dict(bytes=p.stat().st_size,sha256=i.sha(p))});put(p,'changed')
  plan=dict(r8_kit=str(prior),r8_preservation=str(js(self.r/'pins',pins)),logs=str(logs))
  with self.assertRaisesRegex(i.Refusal,'preserved evidence drift'):c.preservation(plan)

if __name__=='__main__':unittest.main()
