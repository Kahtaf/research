"""Actual validator functions; tiny non-executable ELF/APEX-shaped fixtures only."""
import importlib.util,struct,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import verify_root_payload as fixed
from integrate import sha,Refusal
class RootPaths(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir='/srv/android/asus-reviewed-build-kit/r9-exec-r1-fixtures',prefix='root-path-');self.r=Path(self.tmp.name);self.product=self.r/'product';self.apex=self.r/'apex'
  h=bytearray(20);h[:6]=b'\x7fELF\x02\x01';struct.pack_into('<H',h,18,183)
  self.put(self.product,'system/system_ext/bin/adb_root',h);self.init=self.put(self.product,'system/system_ext/etc/init/adb_root.rc',b'fixture')
  self.put(self.product,'system/apex/adbd.capex',b'fixture');self.put(self.apex,'com.android.adbd/bin/adbd',h)
  self.put(self.apex,'apex-info-list.xml',b'<apex-info-list><apex-info moduleName="com.android.adbd" isActive="true" modulePath="/system/apex/adbd.capex"/></apex-info-list>')
  self.put(self.product,'system/build.prop',b'ro.secure=1\nro.debuggable=1\nro.adb.secure=1\n')
  self.paths=['system/system_ext/etc/build.prop','system/product/etc/build.prop']
  for rel in self.paths:self.put(self.product,rel,b'ro.adb.secure=1\n')
 def tearDown(self):self.tmp.cleanup()
 def put(self,base,rel,data):
  p=base/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);return p
 def verify(self,module=fixed):return module.verify(self.product,self.apex,sha(self.init))
 def test_actual_current_property_paths_included(self):self.assertTrue(set(self.paths)<=self.verify()['installed_files'].keys())
 def test_conflicts_rejected_at_each_current_path(self):
  for rel in self.paths:
   self.put(self.product,rel,b'ro.adb.secure=0\n')
   with self.subTest(path=rel),self.assertRaisesRegex(Refusal,'Generated secure userdebug'):self.verify()
   self.put(self.product,rel,b'ro.adb.secure=1\n')
 def test_exact_preimage_demonstrates_previous_gap(self):
  spec=importlib.util.spec_from_file_location('root_before',ROOT/'inputs/root-property-path-fix/preimage.py');before=importlib.util.module_from_spec(spec);spec.loader.exec_module(before)
  self.assertFalse(set(self.paths)<=self.verify(before)['installed_files'].keys())
  for rel in self.paths:
   self.put(self.product,rel,b'ro.adb.secure=0\n');self.verify(before);self.put(self.product,rel,b'ro.adb.secure=1\n')
if __name__=='__main__':unittest.main()
