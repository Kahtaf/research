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
