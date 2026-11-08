from pathlib import Path
import os,sys,socket,subprocess,json,tempfile,struct
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'));import host
results=[]
def server(fault='none',terminal=False):
 a,b=socket.socketpair();a.settimeout(20)
 args=[str(R/'artifacts/session_server'),str(b.fileno()),fault];fds=[b.fileno()];extra=[]
 if terminal:
  x,y=socket.socketpair();x.settimeout(5);args.append(str(y.fileno()));fds.append(y.fileno());extra=[x,y]
 p=subprocess.Popen(args,pass_fds=fds,cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);b.close()
 if extra:extra[1].close()
 return a,p,extra[0] if extra else None

def finish(p):
 out,err=p.communicate(timeout=30);assert p.returncode==0,(out,err,p.returncode);return json.loads(out)
base_frames=host.Frames
for name,fault in [('success','none'),('already_stock','already_stock'),('shortwrite','shortwrite'),('final_mismatch','final_mismatch'),('lost_final_ack','none'),('corrupt_final_ack','none'),('wrong_prior_ack','none'),('fragmented_io','none')]:
 a,p,_=server(fault)
 class FaultFrames(base_frames):
  def receive(self,op,n):
   result=super().receive(op,n)
   if op==0xb4 and name=='lost_final_ack':raise EOFError('injected final receipt loss')
   if op==0xb4 and name=='corrupt_final_ack':return bytes(32)
   if op==0xb2 and name=='wrong_prior_ack':return result[:4]+bytes(32)
   return result
  def send(self,op,data=b''):
   if name!='fragmented_io':return super().send(op,data)
   data=struct.pack('<4sII',b'RSC1',op,len(data))+data
   for off in range(0,len(data),17011):self._limit();self.stream.sendall(data[off:off+17011])
  def read(self,n):
   if name!='fragmented_io':return super().read(n)
   out=bytearray()
   while len(out)<n:
    self._limit();v=self.stream.recv(min(n-len(out),7))
    if not v:raise EOFError()
    out.extend(v)
   return bytes(out)
 host.Frames=FaultFrames
 with tempfile.TemporaryDirectory(dir=R/'artifacts',prefix='host-') as tmp:
  try:record=host._exchange(a,tmp);outcome=record['outcome']
  except host.UnknownOutcome:outcome='UNKNOWN'
  state=finish(p)
  expected='DONE' if name in ('success','fragmented_io') else 'SKIPPED' if name=='already_stock' else 'UNKNOWN'
  assert outcome==expected,(name,outcome,state)
  assert json.loads((Path(tmp)/'attempt.json').read_text())['outcome']=='UNKNOWN'
  receipt=json.loads((Path(tmp)/'receipt.json').read_text())
  assert receipt['outcome']=='UNKNOWN' and receipt['publication_accepted'] is False
  if expected!='UNKNOWN':assert receipt['device_outcome']==expected and record['publication_accepted'] is True
  if name=='wrong_prior_ack':assert state['opens']==0
  if name=='lost_final_ack':assert state['state']=='DONE' and state['writes']==16
  # Reuse of a consumed receipt location fails before any transport send.
  class NoTransport:
   def sendall(self,*_):raise AssertionError('must never send')
  try:host._exchange(NoTransport(),tmp);raise AssertionError('reused attempt')
  except FileExistsError:pass
  results.append(dict(case=name,passed=True,host=outcome,target=state))
host.Frames=base_frames
stock=host._payload()
for name in ['partial_payload_activation','source_hash_override','partition_override','socket_timeout','lost_commit_connection','reconnect_after_unknown','reconnect_after_done']:
 a,p,terminal=server('shortwrite' if name=='reconnect_after_unknown' else 'none',terminal=name.startswith('reconnect'))
 f=host.Frames(a);f.send(0x30);f.receive(0xb0,0)
 if name in ['lost_commit_connection','reconnect_after_unknown','reconnect_after_done']:
  for off in range(0,host.SIZE,host.CHUNK):f.send(0x31,stock[off:off+host.CHUNK]);f.receive(0xb1,0)
  f.send(0x32);f.receive(0xb2,36);f.send(0x33)
  if name=='lost_commit_connection':a.close()
  else:
   try:f.receive(0xb4,32)
   except EOFError:pass
   a.close()
   tf=host.Frames(terminal)
   if name=='reconnect_after_unknown':
    tf.send(0x40);header=tf.read(12);_,op,n=struct.unpack('<4sII',header);assert op==0xc0
    text=tf.read(n).decode();assert 'state=UNKNOWN' in text and 'retry=0' in text
   else:tf.send(0x33);assert terminal.recv(12)==b''
   terminal.close()
 else:
  f.send(0x31,stock[:host.CHUNK]);f.receive(0xb1,0)
  if name=='partial_payload_activation':f.send(0x33)
  if name=='source_hash_override':f.send(0x32,bytes(32))
  if name=='partition_override':f.send(0x34,struct.pack('<I',20))
  assert a.recv(12)==b'';a.close()
 state=finish(p)
 if name not in ['lost_commit_connection','reconnect_after_unknown','reconnect_after_done']:assert state['opens']==0
 if name=='reconnect_after_unknown':assert state['state']=='UNKNOWN' and state['writes']==1
 if name=='reconnect_after_done':assert state['state']=='DONE' and state['writes']==16
 results.append(dict(case=name,passed=True,target=state))
try:host.restore(None,None);raise AssertionError('unarmed profile admitted')
except RuntimeError as e:assert 'Unarmed' in str(e)
results.append(dict(case='production_host_unarmed_refusal',passed=True))
(R/'evidence/host-tests.json').write_text(json.dumps(results,indent=2)+'\n')
print('HOST_PROTOCOL_PASS',len(results))
