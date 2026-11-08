from pathlib import Path
import sys,tempfile,json,socket,struct
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'snapshot/source'));import host
class HelloAfter16Seconds:
 def __init__(self):self.limits=[];self.sent=[];self.closed=False
 def settimeout(self,t):self.timeout=t;self.limits.append(t)
 def sendall(self,b):self.sent.append(struct.unpack_from('<I',b,4)[0])
 def recv(self,n):
  assert self.timeout<16
  raise socket.timeout('model: valid handoff acknowledgement arrives after 16 seconds')
 def close(self):self.closed=True
stream=HelloAfter16Seconds()
with tempfile.TemporaryDirectory(dir=R/'evidence') as tmp:
 try:host._exchange(stream,tmp);raise AssertionError('expected timeout')
 except host.UnknownOutcome:pass
 record=json.loads((Path(tmp)/'receipt.json').read_text());assert record['outcome']=='UNKNOWN' and stream.sent==[0x30] and stream.closed
 result=dict(model_only=True,wall_clock_benchmark=False,production_host_used=True,valid_ack_delay_seconds=16,observed_socket_timeouts=stream.limits,configured_overall_deadline_seconds=300,sent_opcodes=stream.sent,outcome=record['outcome'],retry=False)
(R/'evidence/timeout-model.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
