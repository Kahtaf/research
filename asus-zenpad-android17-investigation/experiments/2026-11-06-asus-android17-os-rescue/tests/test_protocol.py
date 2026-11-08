import socket,struct,sys,threading,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from protocol import *
from test_rescue import RescueTests,ZERO
class ProtocolTests(RescueTests):
 # Own tests plus inherited state-machine checks intentionally avoided by loader below.
 def test_binary_socketpair(self):
  s,b=self.session();s.begin('install-boot',system_verified=True,data_verified=True)
  a,z=socket.socketpair()
  try:
   t=threading.Thread(target=send_frame,args=(a,0,ZERO));t.start();receive_frame(s,z);t.join()
   self.assertEqual(b.writes,[('boot',0,CHUNK)])
  finally:a.close();z.close()
 def test_eof_freezes_without_writes_or_retries(self):
  s,b=self.session();s.begin('install-boot',system_verified=True,data_verified=True)
  a,z=socket.socketpair()
  try:
   a.sendall(HEADER.pack(b'ASR1',0,CHUNK,0)+b'partial');a.shutdown(socket.SHUT_WR)
   with self.assertRaises(TransportLost):receive_frame(s,z)
   self.assertEqual(s.state,State.UNCERTAIN);self.assertFalse(b.writes)
   with self.assertRaises(Refused):receive_frame(s,z)
  finally:a.close();z.close()
 def test_socket_write_loss_preserves_uncertain_error(self):
  s,b=self.session();s.begin('install-boot',system_verified=True,data_verified=True);b.loss='write'
  a,z=socket.socketpair()
  try:
   t=threading.Thread(target=send_frame,args=(a,0,ZERO));t.start()
   with self.assertRaises(TransportLost):receive_frame(s,z)
   t.join();self.assertEqual(s.state,State.UNCERTAIN);self.assertEqual(len(b.writes),1)
  finally:a.close();z.close()
 def test_oversize_header_refused_before_payload(self):
  s,b=self.session();s.begin('install-boot',system_verified=True,data_verified=True)
  a,z=socket.socketpair()
  try:
   a.sendall(HEADER.pack(b'ASR1',0,CHUNK+1,0))
   with self.assertRaises(Refused):receive_frame(s,z)
   self.assertEqual(s.state,State.FAILED);self.assertFalse(b.writes)
  finally:a.close();z.close()
def load_tests(loader,tests,pattern):
 return unittest.TestSuite(ProtocolTests(n) for n in ('test_binary_socketpair','test_eof_freezes_without_writes_or_retries','test_oversize_header_refused_before_payload','test_socket_write_loss_preserves_uncertain_error'))
