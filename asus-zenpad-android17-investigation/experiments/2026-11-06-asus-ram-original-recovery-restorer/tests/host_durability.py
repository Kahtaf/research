from pathlib import Path
import tempfile,socket,subprocess,json,sys,os
from unittest.mock import patch
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'));import host
results=[]
class NoSend:
 def settimeout(self,*_):pass
 def sendall(self,*_):raise AssertionError('transport must not be activated')
with tempfile.TemporaryDirectory(dir=R/'artifacts') as tmp:
 with patch.object(host.os,'fsync',side_effect=OSError('injected fsync failure')):
  try:host._exchange(NoSend(),tmp);raise AssertionError('receipt failure admitted')
  except OSError:pass
 results.append(dict(case='attempt_fsync_failure_prevents_transport',passed=True))
with tempfile.TemporaryDirectory(dir=R/'artifacts') as tmp:
 a,b=socket.socketpair();p=subprocess.Popen([str(R/'artifacts/session_server'),str(b.fileno()),'none'],pass_fds=[b.fileno()],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,cwd=R);b.close()
 real_fsync=os.fsync;calls=0
 def fail_final(fd):
  global calls
  calls+=1
  if calls>=3:raise OSError('final receipt publication failed')
  return real_fsync(fd)
 with patch.object(host.os,'fsync',side_effect=fail_final):
  try:host._exchange(a,tmp);raise AssertionError('must remain unknown')
  except host.UnknownOutcome:pass
 out,err=p.communicate(timeout=30);assert p.returncode==0,(out,err)
 assert json.loads(out)['state']=='DONE'
 assert json.loads((Path(tmp)/'attempt.json').read_text())['outcome']=='UNKNOWN'
 assert not (Path(tmp)/'receipt.json').exists()
 results.append(dict(case='final_receipt_fsync_failure_keeps_durable_unknown',passed=True))
for case in ['short','corrupt','symlink']:
 with tempfile.TemporaryDirectory(dir=R/'artifacts') as tmp:
  root=Path(tmp);(root/'artifacts').mkdir();payload=root/'artifacts/original-recovery.payload'
  if case=='symlink':payload.symlink_to(R/'artifacts/original-recovery.payload')
  else:payload.write_bytes(bytes(10 if case=='short' else host.SIZE))
  with patch.object(host,'ROOT',root):
   try:host._exchange(NoSend(),tmp);raise AssertionError('bad source admitted')
   except (ValueError,OSError):pass
  assert not (root/'attempt.json').exists()
  results.append(dict(case='payload_'+case+'_refused_before_transport',passed=True))
(R/'evidence/host-durability.json').write_text(json.dumps(results,indent=2)+'\n');print('HOST_DURABILITY_PASS',len(results))
