from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from analyze_materials import analyze_materials
H='a'*64
P=[{'name':'adbd','files':[{'path':'bin/adbd','sha256':H}]}]
class Parser(unittest.TestCase):
 def test_diagnostics_between_markers(self):
  t='MATERIAL name=adbd level=bare file=bin/adbd\nlinker: warning\n'+H+'  /mnt/bin/adbd\nMATERIAL_EXIT adbd bare bin/adbd 0\n'
  self.assertTrue(analyze_materials(t,P)[0]['passed'])
 def test_failed_read_is_not_pass(self):
  t='MATERIAL name=adbd level=bare file=bin/adbd\n'+H+'  /mnt/bin/adbd\nMATERIAL_EXIT adbd bare bin/adbd 1\n'
  self.assertFalse(analyze_materials(t,P)[0]['passed'])
 def test_wrong_path_or_missing_end_is_not_pass(self):
  for t in ['MATERIAL name=adbd level=bare file=bin/adbd\n'+H+'  /mnt/other\nMATERIAL_EXIT adbd bare bin/adbd 0\n','MATERIAL name=adbd level=bare file=bin/adbd\n'+H+'  /mnt/bin/adbd\n']:
   self.assertFalse(analyze_materials(t,P)[0]['passed'])
if __name__=='__main__':unittest.main()
