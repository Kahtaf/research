from test_sessions import *
class Guard(Sessions):
 def test_explicit_bindings(self):
  for mode in ['manifest','pin','image','token','closed','descriptor']:
   p=subprocess.run([str(R/'tests/guard'),str(self.root),mode],capture_output=True,text=True,preexec_fn=limits)
   self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(p.stderr,'');self.assertIn('invalidated',p.stdout)
if __name__=='__main__':
 suite=unittest.TestSuite([Guard('test_explicit_bindings')]);r=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(not r.wasSuccessful())
