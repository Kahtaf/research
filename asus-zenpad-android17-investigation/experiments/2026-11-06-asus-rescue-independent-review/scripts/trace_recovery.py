"""Count p10 pread bytes in tiny real-session fixtures; never estimates speed."""
import json,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tests'),str(R/'source')]
import test_adapters as a
import client
import struct
records=[]
class Trace(a.Adapter):
 def collect(self,name,want_hashes):
  self.proc.terminate();out,err=self.proc.communicate(timeout=5);self.proc=None
  reads=[int(line.split('=')[1]) for line in err.splitlines() if line.startswith('RECOVERY_READ bytes=')]
  self.assertEqual(reads,[8192]*want_hashes)
  records.append(dict(case=name,recovery_read_calls=len(reads),recovery_bytes=sum(reads),expected_full_hashes=want_hashes,fixture_recovery_bytes=8192))
 def test_all_skip_includes_per_chunk_recovery(self):
  self.start()
  with self.connect() as s:self.complete(s,0)
  self.collect('four SKIP chunks + two reconciliation + activation + finish + commit',9)
 def test_all_write_includes_per_chunk_recovery(self):
  self.start()
  with self.connect() as s:self.complete(s,2)
  self.collect('four WRITE chunks + two reconciliation + activation + finish + commit',9)
 def test_system_readback_does_not_read_p10(self):
  self.start()
  with self.connect() as s:
   client.send(s.fileno(),6,struct.pack('<II',25,0));client.receive(s.fileno(),0x86);client.receive(s.fileno(),0x87)
  self.collect('SYSTEM readback opcode6',0)
suite=unittest.TestSuite(Trace(n) for n in Trace.__dict__ if n.startswith('test_'))
result=unittest.TextTestRunner(verbosity=2).run(suite)
(R/'evidence/recovery-trace.json').write_text(json.dumps(dict(passed=result.wasSuccessful(),tests=result.testsRun,cases=records,scope='instrumented pread wrapper only; unchanged production session source; synthetic ordinary files; no speed or physical proof'),indent=2)+'\n')
sys.exit(not result.wasSuccessful())
