from pathlib import Path
import errno,json,os,socket,struct,sys,tempfile,unittest
from unittest.mock import patch
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'source'))
import host

class Clock:
    now=1000.0
    def monotonic(self):return self.now

class ModelStream:
    """Protocol/clock model, not a device or throughput benchmark."""
    def __init__(self,clock,delays=None,fragment=False):
        self.clock=clock;self.delays=delays or {};self.buffer=b''
        self.sent=[];self.closed=False;self.pending_delay=0;self.fragment=fragment
    def settimeout(self,n):self.timeout=n
    def sendall(self,data):
        magic,op,n=struct.unpack_from('<4sII',data)
        assert magic==b'RSC1' and len(data)==12+n
        self.sent.append(op);self.pending_delay=self.delays.get(op,0)
        if op==0x30:reply,payload=0xb0,b''
        elif op==0x31:reply,payload=0xb1,b''
        elif op==0x32:reply,payload=0xb2,struct.pack('<I',0)+bytes.fromhex(host.PRIOR_SHA)
        elif op==0x33:reply,payload=0xb4,bytes.fromhex(host.STOCK_SHA)
        else:raise AssertionError(op)
        self.buffer=struct.pack('<4sII',b'RSC1',reply,len(payload))+payload
    def recv(self,n):
        delay=20 if self.fragment else self.pending_delay
        self.pending_delay=0
        if delay>self.timeout:
            self.clock.now+=self.timeout
            raise socket.timeout('modeled phase deadline')
        self.clock.now+=delay
        n=min(n,1) if self.fragment else n
        data,self.buffer=self.buffer[:n],self.buffer[n:]
        return data
    def close(self):self.closed=True

class ContractTests(unittest.TestCase):
    def exchange(self,stream,directory):
        with patch.object(host.time,'monotonic',side_effect=stream.clock.monotonic):
            return host._exchange(stream,directory)
    def test_success_requires_live_publication_return(self):
        stream=ModelStream(Clock())
        with tempfile.TemporaryDirectory() as tmp:
            result=self.exchange(stream,tmp)
            receipt=json.loads((Path(tmp)/'receipt.json').read_text())
            self.assertEqual(result['outcome'],'DONE')
            self.assertTrue(result['publication_accepted'])
            self.assertEqual(receipt['outcome'],'UNKNOWN')
            self.assertEqual(receipt['device_outcome'],'DONE')
            self.assertFalse(receipt['publication_accepted'])
    def test_post_rename_sync_failure_and_storage_loss(self):
        stream=ModelStream(Clock());real_fsync=os.fsync;real_open=os.open
        calls=0;failed=False
        def fsync(fd):
            nonlocal calls,failed
            calls+=1
            if calls==4:
                failed=True
                raise OSError(errno.EIO,'final directory fsync failed')
            return real_fsync(fd)
        def opn(*args,**kwargs):
            if failed:raise OSError(errno.EROFS,'UNKNOWN rewrite unavailable')
            return real_open(*args,**kwargs)
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(host.os,'fsync',side_effect=fsync),patch.object(host.os,'open',side_effect=opn):
                with self.assertRaises(host.UnknownOutcome):self.exchange(stream,tmp)
            receipt=json.loads((Path(tmp)/'receipt.json').read_text())
            attempt=json.loads((Path(tmp)/'attempt.json').read_text())
            self.assertEqual(receipt['outcome'],'UNKNOWN')
            self.assertEqual(receipt['device_outcome'],'DONE')
            self.assertFalse(receipt['publication_accepted'])
            self.assertEqual(attempt['outcome'],'UNKNOWN')
            self.assertEqual(stream.sent.count(0x33),1)
            self.assertTrue(stream.closed)
    def test_valid_16_second_initial_reply(self):
        stream=ModelStream(Clock(),{0x30:16})
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.exchange(stream,tmp)['outcome'],'DONE')
    def test_each_phase_timeout_is_terminal_unknown(self):
        for op,delay in [(0x30,181),(0x31,16),(0x32,61),(0x33,121)]:
            with self.subTest(op=op),tempfile.TemporaryDirectory() as tmp:
                stream=ModelStream(Clock(),{op:delay})
                with self.assertRaises(host.UnknownOutcome):self.exchange(stream,tmp)
                self.assertEqual(stream.sent.count(op),1)
                self.assertTrue(stream.closed)
                receipt=json.loads((Path(tmp)/'receipt.json').read_text())
                self.assertEqual(receipt['outcome'],'UNKNOWN')
                self.assertFalse(receipt['publication_accepted'])
    def test_fragment_activity_does_not_extend_phase(self):
        stream=ModelStream(Clock(),fragment=True)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(host.UnknownOutcome):self.exchange(stream,tmp)
            self.assertLessEqual(stream.clock.now,1180)
            self.assertEqual(stream.sent,[0x30])
    def test_phase_reset_does_not_extend_operation(self):
        clock=Clock();stream=ModelStream(clock)
        with patch.object(host.time,'monotonic',side_effect=clock.monotonic):
            f=host.Frames(stream)
            clock.now+=599;f.begin('handoff');f._limit()
            self.assertEqual(stream.timeout,1)
            clock.now+=1;f.begin('restore')
            with self.assertRaises(TimeoutError):f.send(0x33)
        self.assertEqual(stream.sent,[])
    def test_unqualified_timing_refused_before_any_request(self):
        stream=ModelStream(Clock())
        with patch.object(host,'ARMED',True),tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError,'not physically qualified'):
                host.restore(stream,tmp)
            self.assertEqual(stream.sent,[])
            self.assertEqual(list(Path(tmp).iterdir()),[])

if __name__=='__main__':unittest.main(verbosity=2)
