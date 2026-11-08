from pathlib import Path
import sys,os,tempfile,json,socket,subprocess,errno
from unittest.mock import patch
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'));import host
out=[]
with tempfile.TemporaryDirectory(dir=R/'artifacts',prefix='receipt-edge-') as tmp:
 a,b=socket.socketpair();p=subprocess.Popen([str(R/'artifacts/session_server'),str(b.fileno()),'none'],pass_fds=[b.fileno()],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);b.close()
 real_fsync,real_open=os.fsync,os.open;calls=0;failed=False
 def fsync(fd):
  global calls,failed
  calls+=1
  if calls==4:
   failed=True;raise OSError(errno.EIO,'injected final directory fsync failure after rename')
  return real_fsync(fd)
 def opn(*args,**kwargs):
  if failed:raise OSError(errno.EROFS,'injected storage unavailable for UNKNOWN rewrite')
  return real_open(*args,**kwargs)
 with patch.object(host.os,'fsync',side_effect=fsync),patch.object(host.os,'open',side_effect=opn):
  try:host._exchange(a,tmp);raise AssertionError('unknown expected')
  except host.UnknownOutcome as e:error=str(e)
 stdout,stderr=p.communicate(timeout=30);assert p.returncode==0,(stdout,stderr)
 attempt=json.loads((Path(tmp)/'attempt.json').read_text());receipt=json.loads((Path(tmp)/'receipt.json').read_text())
 assert attempt['outcome']=='UNKNOWN' and receipt['outcome']=='DONE'
 out.append(dict(case='post_rename_directory_fsync_failure_and_unavailable_storage',api_outcome='UNKNOWN',attempt_outcome=attempt['outcome'],visible_receipt_outcome=receipt['outcome'],fsync_calls=calls,target=json.loads(stdout),error=error,final_directory_durability='not established'))
 # Retain exact ordinary-file evidence before fixture cleanup.
 (R/'evidence/receipt-edge-attempt.json').write_text(json.dumps(attempt,indent=2)+'\n')
 (R/'evidence/receipt-edge-visible-final.json').write_text(json.dumps(receipt,indent=2)+'\n')
(R/'evidence/receipt-edges.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
