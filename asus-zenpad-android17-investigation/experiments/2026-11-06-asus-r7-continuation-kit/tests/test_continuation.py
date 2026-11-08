"""Fresh filesystem/process fixtures for the r7 boundary; no production writes."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import integrate as i
import continuation as c
import verify_config_paths as paths

def put(p,data):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data.encode() if isinstance(data,str) else data);return p

def js(p,data):return put(p,json.dumps(data))

class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='TEST_ONLY-',dir=ROOT/'tests');self.r=Path(self.tmp.name)
        r=self.r;logs=r/'logs';logs.mkdir();prior=r/'prior-attempt';prior.mkdir();out=r/'out';out.mkdir()
        actual=json.loads((ROOT/'inputs/r6-terminal-log.json').read_text())['log']
        for ext,data in [('started','2026-11-06T22:26:03.465852+00:00\n'),('finished','2026-11-06T22:28:00.150539+00:00\n'),('exit-code','1\n'),('log',actual)]:put(logs/('full-build-r6.'+ext),data)
        js(prior/'FAILED.json',dict(retry_allowed=False));put(prior/'integration.json','TEST_ONLY integrated receipt')
        put(out/'system.img','TEST_ONLY preserved cache/image')
        old=put(r/'device/sensors/BoardConfig.mk',(ROOT/'inputs/sensor-source/BoardConfig.mk').read_bytes())
        origin=r/'origin';shutil.copytree(ROOT/'inputs/sensor-source',origin)
        post=put(r/'post.mk',(ROOT/'inputs/sensor-BoardConfig.mk').read_bytes())
        before=i.manifest(r/'device');after=dict(before);after['sensors/BoardConfig.mk']={'sha256':c.POST}
        self.p=dict(run_root=str(r),revision='r7',lock=str(put(logs/'full-product-build.lock','')),logs=str(logs),original_pids=[],
                    prior_attempt=str(prior),product_out=str(out),prior_pins=str(r/'prior-pins.json'),sensor_delta=str(ROOT/'inputs/sensor-delta.json'),
                    sensor_origin=str(origin),sensor_postimage=str(post),device=str(r/'device'),prior_staged_receipt=str(js(r/'prior-staged.json',dict(product_after=before))),
                    prior_integration=str(js(r/'prior-integration.json',json.loads((ROOT/'inputs/r6-integration.json').read_text()))),
                    staged_receipt=str(js(r/'staged.json',dict(product_after=after))),sensor_receipt=str(put(r/'sensor-receipt.json','TEST_ONLY')),
                    clean_receipt=str(put(r/'clean.complete','TEST_ONLY prior clean')))
        self.repin_prior()
        template=c.terminal(self.p,describe=True)['review_template'];template.update(reviewed_by_parent=True,reason='TEST_ONLY fixture parent acceptance')
        self.review=js(r/'parent-review/failure.json',template)
    def tearDown(self):self.tmp.cleanup()
    def repin_prior(self):
        pins={name:{str(p):dict(sha256=i.sha(p),bytes=p.stat().st_size) for p in sorted(Path(root).rglob('*')) if p.is_file() and (name!='logs' or p.name.startswith('full-build-r6.'))}
              for name,root in [('logs',self.p['logs']),('attempt_files',self.p['prior_attempt'])]}
        js(self.p['prior_pins'],pins)
    def review_arg(self):return (self.review,i.sha(self.review))
    def test_requires_parent_acceptance_and_exact_terminal(self):
        with self.assertRaisesRegex(i.Refusal,'explicit hash-bound'):c.terminal(self.p)
        d=i.read(self.review);d['reviewed_by_parent']=False;js(self.review,d)
        with self.assertRaisesRegex(i.Refusal,'not explicitly accepted'):c.terminal(self.p,self.review_arg())
        d['reviewed_by_parent']=True;js(self.review,d);c.terminal(self.p,self.review_arg())
        with self.assertRaisesRegex(i.Refusal,'pin mismatch'):c.terminal(self.p,(self.review,'0'*64))
        put(Path(self.p['logs'])/'full-build-r6.exit-code','0\n')
        with self.assertRaisesRegex(i.Refusal,'Unexpected r6 exit'):c.terminal(self.p,self.review_arg())
    def test_missing_terminal_or_failure_and_altered_log_refused(self):
        finished=Path(self.p['logs'])/'full-build-r6.finished';data=finished.read_bytes();finished.unlink()
        with self.assertRaisesRegex(i.Refusal,'actual terminal'):c.terminal(self.p,self.review_arg())
        finished.write_bytes(data);failed=Path(self.p['prior_attempt'])/'FAILED.json';failed.unlink()
        with self.assertRaisesRegex(i.Refusal,'FAILED.json'):c.terminal(self.p,self.review_arg())
        js(failed,dict(retry_allowed=False));put(Path(self.p['logs'])/'full-build-r6.log','timeout guess')
        with self.assertRaisesRegex(i.Refusal,'terminal log changed'):c.terminal(self.p,self.review_arg())
    def test_prior_extra_file_and_changed_image_refused(self):
        extra=put(Path(self.p['prior_attempt'])/'extra','unknown')
        with self.assertRaisesRegex(i.Refusal,'file set changed'):c.terminal(self.p,self.review_arg())
        extra.unlink();put(Path(self.p['product_out'])/'system.img','changed')
        with self.assertRaisesRegex(i.Refusal,'changed since parent'):c.terminal(self.p,self.review_arg())
    def test_used_revision_or_attempt_is_never_reused(self):
        marker=put(Path(self.p['logs'])/'full-build-r7.started','old')
        with self.assertRaisesRegex(i.Refusal,'Revision already used'):i.revision_unused(self.p)
        marker.unlink();(self.r/'attempt').mkdir()
        with self.assertRaisesRegex(i.Refusal,'Previous attempt'):i.revision_unused(self.p)
    def test_lock_refuses_and_native_identity_refuses_before_writes(self):
        with open(self.p['lock'],'r+') as held:
            fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaisesRegex(i.Refusal,'LIVE_BUILD_LOCK'):i.execute(self.p,self.r,True,self.review_arg())
        self.assertFalse((self.r/'attempt').exists())
        if sys.platform=='linux':
            child=subprocess.Popen([sys.executable,'-B','-c',"import ctypes,sys;ctypes.CDLL(None).prctl(15,b'ninja',0,0,0);print('ready',flush=True);sys.stdin.read()"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
            try:
                self.assertEqual(child.stdout.readline().strip(),'ready')
                with self.assertRaisesRegex(i.Refusal,'LIVE_NATIVE_BUILD'):i.execute(self.p,self.r,True,self.review_arg())
                self.assertFalse((self.r/'attempt').exists())
            finally:child.communicate('done',timeout=5)
    def test_preservation_and_only_one_source_write(self):
        attempt=self.r/'attempt';attempt.mkdir();original=i.manifest(self.r/'device');image=Path(self.p['product_out'])/'system.img';ino=image.stat().st_ino
        c.preserve(self.p,attempt,c.terminal(self.p,self.review_arg()))
        self.assertEqual(i.sha(attempt/'before/sensor-BoardConfig.mk'),c.PRE)
        with patch.object(i,'verify_integrated',return_value=dict(TEST_ONLY=True)):
            c.apply(self.p,attempt)
        self.assertEqual(image.stat().st_ino,ino)
        self.assertEqual(image.read_text(),'TEST_ONLY preserved cache/image')
        changed=[p for p,row in original.items() if i.manifest(self.r/'device')[p]!=row]
        self.assertEqual(changed,['sensors/BoardConfig.mk'])
        receipt=i.read(attempt/'integration.json');self.assertEqual(len(receipt['source_writes']),1)
        self.assertEqual(receipt['source_writes'][0]['after'],c.POST)
        with self.assertRaisesRegex(i.Refusal,'r3 source changed'):c.apply(self.p,attempt)
    def test_delta_refuses_old_bug_or_unrelated_change(self):
        post=Path(self.p['sensor_postimage']);post.write_bytes((ROOT/'inputs/sensor-source/BoardConfig.mk').read_bytes())
        with self.assertRaisesRegex(i.Refusal,'delta pin'):c.sensor_delta(self.p)
    def test_real_make_evaluates_fixed_paths_with_my_dir_unavailable(self):
        make=shutil.which('make');self.assertIsNotNone(make)
        for file,policy,manifest in [(ROOT/'inputs/sensor-source/BoardConfig.mk','/sepolicy','/manifest.xml'),(ROOT/'inputs/sensor-BoardConfig.mk','device/asus/p00a/sensors/sepolicy','device/asus/p00a/sensors/manifest.xml')]:
            text=f'include {file}\n$(info POLICY=$(BOARD_VENDOR_SEPOLICY_DIRS))\n$(info MANIFEST=$(DEVICE_MANIFEST_FILE))\nall:;@:\n'
            result=subprocess.run([make,'-j1','-f','-'],input=text,text=True,capture_output=True,check=True)
            self.assertIn('POLICY='+policy+'\n',result.stdout);self.assertIn('MANIFEST='+manifest+'\n',result.stdout)
    @unittest.skipUnless(sys.platform=='linux','real inherited FD and /proc parent identity fixture')
    def test_supervisor_inherits_lock_and_consumes_child_once(self):
        # Isolate the large source audit; exercise the actual supervisor, preserve,
        # sole source write, inherited lock checker and subprocess lifecycle.
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
        put(self.r/'scripts/build.sh',script);js(self.r/'inputs/plan.json',self.p)
        pins={str(p.relative_to(self.r)):i.sha(p) for folder in ['scripts','inputs'] for p in (self.r/folder).rglob('*') if p.is_file()}
        js(self.r/'inputs/kit-pins.json',pins)
        with patch.object(i,'audit_inputs',return_value=dict(TEST_ONLY=True)),patch.object(i,'verify_integrated',return_value=dict(TEST_ONLY=True)):
            result=i.execute(self.p,self.r,True,self.review_arg())
        self.assertEqual(result['mode'],'PARENT_EXECUTE');self.assertTrue((self.r/'attempt/build-consumed').is_file())
        with self.assertRaisesRegex(i.Refusal,'Revision already used'):i.execute(self.p,self.r,True,self.review_arg())

class PathTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='TEST_ONLY-',dir=ROOT/'tests');self.r=Path(self.tmp.name)
        sensor=self.r/'aosp/device/asus/p00a/sensors';shutil.copytree(ROOT/'inputs/sensor-source',sensor)
        shutil.copyfile(ROOT/'inputs/sensor-BoardConfig.mk',sensor/'BoardConfig.mk')
        self.p=dict(aosp=str(self.r/'aosp'),staged_receipt=str(js(self.r/'staged.json',dict(product_after={'sensors/'+k:v for k,v in i.manifest(sensor).items()}))))
        self.values={k:'' for k in paths.POLICY_VARS+paths.MANIFEST_VARS}
        self.values.update(BOARD_VENDOR_SEPOLICY_DIRS='device/asus/p00a/sensors/sepolicy',DEVICE_MANIFEST_FILE='device/asus/p00a/sensors/manifest.xml')
        self.vars=self.r/'actual-fixture.vars'
    def tearDown(self):self.tmp.cleanup()
    def verify(self):
        self.vars.write_text(''.join(k+"='"+v+"'\n" for k,v in self.values.items()));return paths.verify(self.vars,self.p)
    def test_relative_present_exact_paths_pass_and_bad_variants_fail(self):
        self.assertTrue(self.verify()['source_configuration_paths_verified'])
        for key,bad in [('BOARD_VENDOR_SEPOLICY_DIRS','/sepolicy'),('DEVICE_MANIFEST_FILE','/manifest.xml'),('BOARD_ODM_SEPOLICY_DIRS','../outside'),('PRODUCT_PRIVATE_SEPOLICY_DIRS','missing'),('DEVICE_MANIFEST_FILE','device/asus/p00a/sensors/manifest.xml device/asus/p00a/sensors/manifest.xml')]:
            old=self.values[key];self.values[key]=bad
            with self.assertRaisesRegex(i.Refusal,'CONFIG_PATH_ERROR'):self.verify()
            self.values[key]=old
    def test_missing_sensor_duplicate_combined_vendor_and_symlink_escape(self):
        self.values['BOARD_VENDOR_SEPOLICY_DIRS']=''
        with self.assertRaisesRegex(i.Refusal,'exact sensor policy'):self.verify()
        self.values['BOARD_VENDOR_SEPOLICY_DIRS']='device/asus/p00a/sensors/sepolicy';self.values['BOARD_SEPOLICY_DIRS']=self.values['BOARD_VENDOR_SEPOLICY_DIRS']
        with self.assertRaisesRegex(i.Refusal,'duplicate effective'):self.verify()
        self.values['BOARD_SEPOLICY_DIRS']='';(self.r/'aosp/escape').symlink_to(self.r)
        self.values['BOARD_ODM_SEPOLICY_DIRS']='escape'
        with self.assertRaisesRegex(i.Refusal,'source path escape'):self.verify()
    def test_postimage_and_policy_bytes_are_mandatory(self):
        board=self.r/'aosp/device/asus/p00a/sensors/BoardConfig.mk';board.write_bytes((ROOT/'inputs/sensor-source/BoardConfig.mk').read_bytes())
        with self.assertRaisesRegex(i.Refusal,'not r7 postimage'):self.verify()
        shutil.copyfile(ROOT/'inputs/sensor-BoardConfig.mk',board)
        put(board.parent/'sepolicy/p00a_accelerometer.te','changed policy')
        with self.assertRaisesRegex(i.Refusal,'policy bytes differ'):self.verify()

class SelectionAndSealTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='TEST_ONLY-',dir=ROOT/'tests');self.r=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_pins_refuse_extra_script_and_changed_validator(self):
        put(self.r/'scripts/validator.py','TEST_ONLY validator')
        put(self.r/'inputs/receipt.json','{}')
        pins={str(p.relative_to(self.r)):i.sha(p) for d in ['scripts','inputs'] for p in (self.r/d).rglob('*') if p.is_file()}
        js(self.r/'inputs/kit-pins.json',pins);i.verify_pins(self.r)
        extra=put(self.r/'scripts/extra.py','unreviewed')
        with self.assertRaisesRegex(i.Refusal,'file set changed'):i.verify_pins(self.r)
        extra.unlink();put(self.r/'scripts/validator.py','weakened')
        with self.assertRaisesRegex(i.Refusal,'pin changed'):i.verify_pins(self.r)
    def test_exact_sensor_selection_requires_fix_and_unchanged_policy(self):
        from r3_inputs import sensor_selection
        p=i.read(ROOT/'inputs/plan.json')
        p.update(staging=str(self.r/'stage'),sensor_receipt=str(ROOT/'inputs/sensor-selection.json'),
                 sensor_origin=str(ROOT/'inputs/sensor-source'),sensor_delta=str(ROOT/'inputs/sensor-delta.json'),
                 sensor_postimage=str(ROOT/'inputs/sensor-BoardConfig.mk'),previous_staged_receipt=str(ROOT/'inputs/r2-STAGED.json'),
                 previous_product_inputs=str(ROOT/'inputs/r2-product'))
        candidate=self.r/'stage/product-device';shutil.copytree(ROOT/'inputs/sensor-source',candidate/'sensors')
        mk=(candidate/'sensors/sensors.mk').read_bytes()
        for mod in [b'android.hardware.sensors@1.0-service',b'android.hardware.sensors@1.0-impl']:mk=mk.replace(mod,mod+b':64')
        put(candidate/'sensors/sensors.mk',mk);shutil.copyfile(ROOT/'inputs/sensor-BoardConfig.mk',candidate/'sensors/BoardConfig.mk')
        receipt=i.read(ROOT/'inputs/sensor-selection.json')
        for rel,suffix in receipt['suffixes'].items():put(candidate/rel,(ROOT/'inputs/r2-product'/rel).read_bytes()+suffix.encode())
        staged=i.read(ROOT/'inputs/STAGED.json');self.assertEqual(len(sensor_selection(p,staged)),12)
        shutil.copyfile(ROOT/'inputs/sensor-source/BoardConfig.mk',candidate/'sensors/BoardConfig.mk')
        with self.assertRaisesRegex(i.Refusal,'Exact sensor'):sensor_selection(p,staged)
        shutil.copyfile(ROOT/'inputs/sensor-BoardConfig.mk',candidate/'sensors/BoardConfig.mk')
        put(candidate/'sensors/sepolicy/p00a_accelerometer.te','allow unreviewed;')
        with self.assertRaisesRegex(i.Refusal,'Exact sensor'):sensor_selection(p,staged)
