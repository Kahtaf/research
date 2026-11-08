"""Own callback variant; unchanged RSC1 sequencing comes from the pinned client.
No target subprocess or CLI. Parent opens the transport only after prepare_source.
"""
import hashlib,json,os,struct
import bounded_client as client
from contextlib import ExitStack
from journal import write_all
CHUNK=client.CHUNK
parse,status,reconcile,send,receive=client.parse,client.status,client.reconcile,client.send,client.receive

def _prepare_source(b,index,source,reviewed_sha,stop_after=None):
 rows=parse(b)
 if index is None or not 0<=index<len(rows):raise ValueError('image index')
 row=rows[index]
 if stop_after is not None and not 1<=stop_after<=row['count']:raise ValueError('bounded positive partial trial chunk count required')
 if source.profile['role']!=index or source.profile['size']!=row['size'] or source.profile['sha256']!=reviewed_sha:raise ValueError('fixed source role/size/hash mismatch')
 full,chunks=source.preflight()
 if full!=row['full'] or full.hex()!=reviewed_sha or chunks!=row['chunks']:raise ValueError('raw source does not match reviewed manifest')
 return (hashlib.sha256(b).digest(),index,id(source),reviewed_sha,stop_after)

def prepare_source(b,index,source,reviewed_sha,stop_after=None):
 try:
  result=_prepare_source(b,index,source,reviewed_sha,stop_after)
  source.complete_phase()
  return result
 except BaseException:
  source.close();raise

def record_unknown(fd,evidence):
 fd.poison()  # In-memory truth is terminal even if the evidence sink is broken.
 try:
  write_all(evidence,json.dumps({'outcome':'UNKNOWN','possible_partition_modification':fd.possible_partition_modification,'automatic_retry':False})+'\n')
  evidence.flush();os.fsync(evidence.fileno())
  return True
 except BaseException:return False

def publish_success(fd,evidence):
 # The line is a publication candidate until flush/fsync and the deadline check
 # return. A later publication/close failure still poisons and appends UNKNOWN.
 fd.check()
 write_all(evidence,json.dumps({'outcome':'SUCCESS','commit_receipt':fd.commit_receipt,'possible_partition_modification':fd.possible_partition_modification})+'\n')
 evidence.flush();fd.check();os.fsync(evidence.fileno());fd.check()

def write_image(fd,b,p10,index,source,reviewed_sha,evidence,inverse_from=None,stop_after=None,prepared=None,*,budgets,finalize=True):
 try:
  with ExitStack() as owned_source:
   owned_source.callback(source.close)
   expected=(hashlib.sha256(b).digest(),index,id(source),reviewed_sha,stop_after)
   if prepared is None:prepared=prepare_source(b,index,source,reviewed_sha,stop_after)
   if prepared!=expected:raise ValueError('prepared source/selection mismatch')
   if source.consumed:raise ValueError('prepared source already consumed; fresh preflight and reconciliation required')
   source.set_phase(fd.phase)
   source.check();source.complete_phase();source.consumed=True
   write_all(evidence,json.dumps({'status':status(fd)})+'\n');evidence.flush()
   fd.complete_phase()
   fd.set_phase(budgets.start('reconciliation'))
   token,same,row=reconcile(fd,b,p10,index,inverse_from)
   write_all(evidence,json.dumps({'idle_proven':True,'reconciled_matching_chunks':sum(same),'manifest':hashlib.sha256(b).hexdigest(),'p10':p10.hex(),'image':index,'explicit_inverse_from':inverse_from})+'\n');evidence.flush();os.fsync(evidence.fileno())
   fd.complete_phase()
   transfer=budgets.start('transfer')
   fd.set_phase(transfer);source.set_phase(transfer)
   send(fd,3,token);receive(fd,0x83)
   source.check()
   for i,match in enumerate(same):
    n=min(CHUNK,row['size']-i*CHUNK);data=source.read_chunk(i)
    if len(data)!=n or hashlib.sha256(data).digest()!=row['chunks'][i*32:i*32+32]:raise ValueError('source changed')
    send(fd,7 if match else 4,b'' if match else data)
    ack=receive(fd,0x84)
    if len(ack)!=8 or struct.unpack('<II',ack)[0]!=i:raise ValueError('ack sequence')
    write_all(evidence,json.dumps({'chunk':i,'skipped':bool(struct.unpack('<II',ack)[1])})+'\n');evidence.flush()
    if stop_after is not None and i+1==stop_after:
     write_all(evidence,json.dumps({'partial_trial_stopped':i+1,'whole_partition_verified':False,'reconciliation_required':True})+'\n');evidence.flush();os.fsync(evidence.fileno());fd.poison();return
   source.check();source.complete_phase();fd.complete_phase()
   fd.set_phase(budgets.start('whole_image_hash'))
   send(fd,5);got=receive(fd,0x85)
   if got!=row['full']:raise ValueError('whole readback mismatch')
   send(fd,9,got)
   if receive(fd,0x89)!=got:raise ValueError('commit receipt mismatch')
   fd.commit_receipt=got.hex();fd.outcome='COMMIT_RECEIVED'
   write_all(evidence,json.dumps({'whole_partition_verified':got.hex(),'commit_receipt_verified':got.hex(),'intermediate':True})+'\n');evidence.flush();fd.check()
  fd.check()  # Includes source-close guard latency/failure before publication.
  if finalize:
   publish_success(fd,evidence)
   fd.complete_phase()
   fd.outcome='VERIFIED_COMMIT_RECEIPT'
 except BaseException:
  record_unknown(fd,evidence)
  raise
