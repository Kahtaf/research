"""Own callback variant; unchanged RSC1 sequencing comes from the pinned client.
No target subprocess or CLI. Parent opens the transport only after prepare_source.
"""
import hashlib,json,os,struct
from pinned import client
CHUNK=client.CHUNK
parse,status,reconcile,send,receive=client.parse,client.status,client.reconcile,client.send,client.receive

def prepare_source(b,index,source,reviewed_sha,stop_after=None):
 rows=parse(b)
 if index is None or not 0<=index<len(rows):raise ValueError('image index')
 row=rows[index]
 if stop_after is not None and not 1<=stop_after<=row['count']:raise ValueError('bounded positive partial trial chunk count required')
 if source.profile['role']!=index or source.profile['size']!=row['size'] or source.profile['sha256']!=reviewed_sha:raise ValueError('fixed source role/size/hash mismatch')
 full,chunks=source.preflight()
 if full!=row['full'] or full.hex()!=reviewed_sha or chunks!=row['chunks']:raise ValueError('raw source does not match reviewed manifest')
 return (hashlib.sha256(b).digest(),index,id(source),reviewed_sha,stop_after)

def write_image(fd,b,p10,index,source,reviewed_sha,evidence,inverse_from=None,stop_after=None,prepared=None):
 expected=(hashlib.sha256(b).digest(),index,id(source),reviewed_sha,stop_after)
 if prepared is None:prepared=prepare_source(b,index,source,reviewed_sha,stop_after)
 if prepared!=expected:raise ValueError('prepared source/selection mismatch')
 if source.consumed:raise ValueError('prepared source already consumed; fresh preflight and reconciliation required')
 source.check();source.consumed=True
 evidence.write(json.dumps({'status':status(fd)})+'\n');evidence.flush()
 token,same,row=reconcile(fd,b,p10,index,inverse_from)
 evidence.write(json.dumps({'idle_proven':True,'reconciled_matching_chunks':sum(same),'manifest':hashlib.sha256(b).hexdigest(),'p10':p10.hex(),'image':index,'explicit_inverse_from':inverse_from})+'\n');evidence.flush();os.fsync(evidence.fileno())
 send(fd,3,token);receive(fd,0x83)
 source.check()
 try:
  for i,match in enumerate(same):
   n=min(CHUNK,row['size']-i*CHUNK);data=source.read_chunk(i)
   if len(data)!=n or hashlib.sha256(data).digest()!=row['chunks'][i*32:i*32+32]:raise ValueError('source changed')
   send(fd,7 if match else 4,b'' if match else data)
   ack=receive(fd,0x84)
   if len(ack)!=8 or struct.unpack('<II',ack)[0]!=i:raise ValueError('ack sequence')
   evidence.write(json.dumps({'chunk':i,'skipped':bool(struct.unpack('<II',ack)[1])})+'\n');evidence.flush()
   if stop_after is not None and i+1==stop_after:
    evidence.write(json.dumps({'partial_trial_stopped':i+1,'whole_partition_verified':False,'reconciliation_required':True})+'\n');evidence.flush();os.fsync(evidence.fileno());return
  source.check()
  send(fd,5);got=receive(fd,0x85)
  if got!=row['full']:raise ValueError('whole readback mismatch')
  send(fd,9,got)
  if receive(fd,0x89)!=got:raise ValueError('commit receipt mismatch')
  evidence.write(json.dumps({'whole_partition_verified':got.hex()})+'\n');evidence.flush();os.fsync(evidence.fileno())
 finally:source.close()
