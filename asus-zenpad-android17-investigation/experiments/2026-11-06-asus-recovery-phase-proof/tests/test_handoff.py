from test_sessions import *
class Handoff(Sessions):
 def test_exact_exec_and_lock(self):
  for mode in ['pair','five','uncertain']:
   a,b=socket.socketpair()
   q=subprocess.Popen([str(R/'tests/handoff'),str(self.root),str(b.fileno()),mode],pass_fds=[b.fileno()],stdout=subprocess.PIPE,stderr=subprocess.PIPE,preexec_fn=limits);b.close()
   out,err=q.communicate(timeout=8);self.assertEqual(err,b'')
   self.assertEqual(q.returncode,91 if mode=='pair' else 0)
   self.assertEqual(a.recv(16),b'HANDOFF' if mode=='pair' else b'');a.close()
if __name__=='__main__':
 suite=unittest.TestSuite([Handoff('test_exact_exec_and_lock')]);r=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(not r.wasSuccessful())
