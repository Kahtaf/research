"""Behavioral fixtures; these never count as native product execution."""
import fcntl,gzip,json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import integrate as i
import continuation as c
from compiler_channel import commands_for

def put(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data.encode() if isinstance(data,str) else data);return p
def js(p,d):return put(p,json.dumps(d))
class R8Tests(unittest.TestCase):
 def setUp(self):
  self.native_fixture=patch.object(i,'native_processes',return_value=[]);self.native_fixture.start();self.addCleanup(self.native_fixture.stop)
  self.tmp=tempfile.TemporaryDirectory(prefix='TEST_ONLY-',dir=ROOT/'tests');r=self.r=Path(self.tmp.name)
  prior=r/'r7';(prior/'attempt').mkdir(parents=True);js(prior/'attempt/FAILED.json',dict(retry_allowed=False))
  logs=r/'logs';logs.mkdir();out=r/'out';out.mkdir();put(out/'system.img','TEST_ONLY preserved image')
  # A hash-bound fixture tests terminal integrity without exporting a full log.
  actual='TEST_ONLY actual terminal failure\n'
  fixture_log=put(r/'fixture-log',actual)
  self.log_fixture=patch.object(c,'LOG',i.sha(fixture_log));self.log_fixture.start();self.addCleanup(self.log_fixture.stop)
  for ext,data in [('started','2026-11-06T22:46:58+00:00'),('finished',c.END),('exit-code','1'),('log',actual)]:put(logs/('full-build-r7.'+ext),data)
  shutil.copytree(ROOT/'inputs/r8-preimages',r/'device');shutil.copytree(ROOT/'inputs/r8-preimages',r/'inputs/r8-preimages');shutil.copytree(ROOT/'inputs/r8-postimages',r/'stage/product-device')
  put(r/'inputs/lmkd-functional/vendor-file-contexts.additions',(ROOT/'inputs/lmkd-functional/vendor-file-contexts.additions').read_bytes())
  before=i.manifest(r/'device');after=i.manifest(r/'stage/product-device')
  self.p=dict(run_root=str(r),revision='r8',lock=str(put(logs/'full-product-build.lock','')),logs=str(logs),original_pids=[],product_out=str(out),r7_kit=str(prior),prior_attempt=str(prior/'attempt'),r7_preservation=str(r/'preservation.json'),device=str(r/'device'),staging=str(r/'stage'),r8_delta=str(js(r/'deltas.json',i.read(ROOT/'inputs/r8-delta.json'))),r7_staged_receipt=str(js(r/'old-stage.json',dict(product_after=before))),staged_receipt=str(js(r/'stage.json',dict(product_after=after))),r7_integration=str(js(r/'r7-integration.json',{})),sensor_receipt=str(js(r/'sensor.json',{})),sensor_delta=str(js(r/'sensor-delta.json',{})),clean_receipt=str(put(r/'clean.complete','TEST_ONLY')))
  self.repin();template=c.terminal(self.p,describe=True)['review_template'];template.update(reviewed_by_parent=True,reason='TEST_ONLY acceptance');self.review=js(r/'parent-review/failure.json',template)
 def tearDown(self):self.tmp.cleanup()
 def repin(self):
  p=self.p
  js(p['r7_preservation'],dict(attempt_files={str(f):dict(sha256=i.sha(f),bytes=f.stat().st_size) for f in (Path(p['r7_kit'])/'attempt').rglob('*') if f.is_file()},logs={str(f):dict(sha256=i.sha(f),bytes=f.stat().st_size) for f in Path(p['logs']).glob('full-build-r7.*')},frozen_evidence={}))
 def review_arg(self):return self.review,i.sha(self.review)
 def test_exact_parent_review_and_terminal_mutations(self):
  with self.assertRaisesRegex(i.Refusal,'hash-bound'):c.terminal(self.p)
  c.terminal(self.p,self.review_arg())
  with self.assertRaisesRegex(i.Refusal,'hash mismatch'):c.terminal(self.p,(self.review,'0'*64))
  d=i.read(self.review);d['reviewed_by_parent']=False;js(self.review,d)
  with self.assertRaisesRegex(i.Refusal,'not accepted'):c.terminal(self.p,self.review_arg())
 def test_changed_images_extra_attempt_and_changed_log_refused(self):
  extra=put(Path(self.p['r7_kit'])/'attempt/extra','unknown')
  with self.assertRaisesRegex(i.Refusal,'file set drift'):c.terminal(self.p,self.review_arg())
  extra.unlink();put(Path(self.p['product_out'])/'system.img','changed')
  with self.assertRaisesRegex(i.Refusal,'changed since parent'):c.terminal(self.p,self.review_arg())
  put(Path(self.p['logs'])/'full-build-r7.log','changed')
  with self.assertRaisesRegex(i.Refusal,'terminal log changed'):c.terminal(self.p,self.review_arg())
 def test_only_two_source_writes_and_preservation(self):
  before=i.manifest(self.p['device']);out=Path(self.p['product_out'])/'system.img';inode=out.stat().st_ino;attempt=self.r/'attempt';attempt.mkdir()
  c.preserve(self.p,attempt,c.terminal(self.p,self.review_arg()))
  with patch.object(i,'verify_integrated',return_value=dict(TEST_ONLY=True)):c.apply(self.p,attempt)
  self.assertEqual(set(before),{c.WPA,c.CONTEXT});self.assertEqual(i.manifest(self.p['device']),i.read(self.p['staged_receipt'])['product_after']);self.assertEqual(out.stat().st_ino,inode)
  self.assertEqual(len(i.read(attempt/'integration.json')['source_writes']),2)
  for rel,row in i.read(self.p['r8_delta']).items():self.assertEqual(i.sha(attempt/'before'/rel),row['before'])
  with self.assertRaisesRegex(i.Refusal,'preimage changed'):c.apply(self.p,attempt)
 def test_unrelated_delta_and_blanket_suppression_refused(self):
  c.deltas(self.p);post=Path(self.p['staging'])/'product-device'/c.WPA;post.write_bytes(post.read_bytes()+b'\n#pragma clang diagnostic ignored "-Wextra"\n')
  rows=i.read(self.p['r8_delta']);rows[c.WPA]['after']=i.sha(post);js(self.p['r8_delta'],rows)
  with self.assertRaisesRegex(i.Refusal,'only the upstream'):c.deltas(self.p)
 def test_lock_and_consumed_revision_refused(self):
  with open(self.p['lock'],'r+') as held:
   fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
   with self.assertRaisesRegex(i.Refusal,'LIVE_BUILD_LOCK'):i.execute(self.p,self.r,True,self.review_arg())
  self.assertFalse((self.r/'attempt').exists());put(Path(self.p['logs'])/'full-build-r8.started','TEST_ONLY')
  with self.assertRaisesRegex(i.Refusal,'Revision already used'):i.revision_unused(self.p)
 @unittest.skipUnless(sys.platform=='linux','requires actual /proc lock ancestry')
 def test_actual_supervisor_lock_inheritance_and_one_shot(self):
  script=f'''#!/bin/bash
set -e
python3 -B {ROOT}/scripts/check_launch.py {self.r}
if python3 -B {ROOT}/scripts/check_launch.py {self.r}; then exit 97; fi
python3 -B - <<'END'
import json,hashlib
from pathlib import Path
r=Path({str(self.r)!r});v=r/'attempt/validation';v.mkdir()
p=r/'attempt/integration.json'
(v/'complete.json').write_text(json.dumps(dict(flash_ready=False,integration_receipt_sha256=hashlib.sha256(p.read_bytes()).hexdigest())))
END
'''
  put(self.r/'scripts/build.sh',script);js(self.r/'inputs/plan.json',self.p);js(self.r/'inputs/kit-pins.json',{str(p.relative_to(self.r)):i.sha(p) for d in ['inputs','scripts'] for p in (self.r/d).rglob('*') if p.is_file()})
  with patch.object(i,'audit_inputs',return_value=dict(TEST_ONLY=True)),patch.object(i,'verify_integrated',return_value=dict(TEST_ONLY=True)):
   self.assertEqual(i.execute(self.p,self.r,True,self.review_arg())['mode'],'PARENT_EXECUTE')
  self.assertTrue((self.r/'attempt/build-consumed').is_file())
  with self.assertRaisesRegex(i.Refusal,'Revision already used'):i.execute(self.p,self.r,True,self.review_arg())
 def test_completed_commands_exclude_pending_failed_and_dependencies(self):
  a=self.r/'attempt';js(a/'started.json',{});js(a/'integration.json',{});f=a/'native-evidence/phase';f.mkdir(parents=True)
  with gzip.open(f/'verbose.log.gz','wt') as z:z.write('verbose: ninja: [1/3] clang -o pending source.c\n[1/3] clang -c -o good source.c\n[2/3] clang -o bad bad.c\nFAILED: bad\n[3/3] clang++ -o link good\n')
  js(f/'receipt.json',dict(attempt_started_sha256=i.sha(a/'started.json'),integration_sha256=i.sha(a/'integration.json'),files={'verbose.log.gz':dict(sha256=i.sha(f/'verbose.log.gz'),bytes=(f/'verbose.log.gz').stat().st_size)}))
  commands,_=commands_for(self.r,{'pending','good','bad','link'});self.assertEqual(set(commands),{'good','link'});self.assertEqual(commands['good'],['clang -c -o good source.c'])
  put(f/'verbose.log.gz','changed')
  with self.assertRaisesRegex(i.Refusal,'evidence changed'):commands_for(self.r,{'good'})
 def test_phase_ninja_join_rejects_a_different_current_execution(self):
  from verify_product_r3 import log_entries
  a=self.r/'attempt';js(a/'started.json',{});js(a/'integration.json',{});f=a/'native-evidence/phase';f.mkdir(parents=True)
  with gzip.open(f/'verbose.log.gz','wt') as z:z.write('[1/1] clang -c -o obj source.c\n')
  put(f/'.ninja_log','# ninja log v5\n0\t1\t100\tobj\ta1\n')
  js(f/'receipt.json',dict(attempt_started_sha256=i.sha(a/'started.json'),integration_sha256=i.sha(a/'integration.json'),files={n:dict(sha256=i.sha(f/n),bytes=(f/n).stat().st_size) for n in ['verbose.log.gz','.ninja_log']}))
  entries=log_entries(f/'.ninja_log',{'obj'});self.assertEqual(set(commands_for(self.r,{'obj'},entries)[0]),{'obj'})
  entries['obj']['command_hash']='b2';self.assertEqual(commands_for(self.r,{'obj'},entries)[0],{})
 def test_capture_preserves_failed_phase_and_refuses_overwrite(self):
  from capture_build_evidence import capture
  a=self.r/'attempt';js(a/'started.json',{});js(a/'integration.json',{});out=self.r/'aosp/out';out.mkdir(parents=True)
  with gzip.open(out/'verbose.log.gz','wt') as z:z.write('[1/1] clang -c -o obj source.c\n')
  put(out/'.ninja_log','# ninja log v5\n');js(self.r/'inputs/plan.json',dict(aosp=str(out.parent)))
  capture(self.r,'phase',1)
  self.assertEqual(i.read(a/'native-evidence/phase/receipt.json')['exit_code'],1)
  with self.assertRaises(FileExistsError):capture(self.r,'phase',1)
