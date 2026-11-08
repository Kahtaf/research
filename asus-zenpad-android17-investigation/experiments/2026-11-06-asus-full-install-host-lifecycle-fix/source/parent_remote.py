"""Parent-only transport adapter. PLAN ONLY by default. Never retries or reboots.
Execute only after parent has selected and reviewed the current authenticated ADB transport."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
import source_client as client
from sources import RemoteSource,local_source
from contextlib import ExitStack
from journal import BoundedJournal,write_all
from bounded_io import Budgets,PipeSession,positive,reap_owned
import time,stat
def features_owned(command,phase,cleanup):
 phase.check()
 proc=subprocess.Popen(command+['features'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
 io=None
 try:
  try:
   io=PipeSession(proc.stdout.fileno(),proc.stdin.fileno(),phase,stderr=proc.stderr.fileno(),process=proc)
   proc.stdin.close()
   output=io.read_stream_end(4096)
   phase.check();code=proc.wait(timeout=max(0.000001,phase.deadline-time.monotonic()));phase.check()
   if code:raise RuntimeError('owned feature child exit='+str(code))
  finally:reap_owned(proc,cleanup)
  io.close();phase.check()
  return output.decode().strip().split(',')
 except BaseException:
  if io is not None:io.poison()
  raise
 finally:
  if io is not None and not io.closed:io.close()

def record_terminal_unknown(fd,evidence,path,identity):
 if client.record_unknown(fd,evidence):return
 # A completed close may report failure or return past the deadline. Append
 # only to the same owned regular evidence inode, never to a substituted path.
 if evidence is None or identity is None or not evidence.stream.closed:return
 rawfd=None
 try:
  rawfd=os.open(path,os.O_WRONLY|os.O_APPEND|os.O_NOFOLLOW|os.O_NONBLOCK)
  info=os.fstat(rawfd)
  if (not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or
      (info.st_dev,info.st_ino)!=identity or info.st_size>evidence.limit):return
  with os.fdopen(rawfd,'a',encoding='utf-8') as raw:
   rawfd=None
   client.record_unknown(fd,BoundedJournal(raw,evidence.limit-info.st_size))
 except BaseException:pass  # Poison is already authoritative if disk is broken.
 finally:
  if rawfd is not None:
   try:os.close(rawfd)
   except OSError:pass

def run(stack):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('operation',choices=['status','readback','reconcile','write'])
 p.add_argument('--io-budgets',type=Path);p.add_argument('--io-budgets-sha256')
 p.add_argument('--adb',type=Path);p.add_argument('--adb-sha256');p.add_argument('--transport-id',type=int)
 p.add_argument('--contract',type=Path);p.add_argument('--contract-sha256');p.add_argument('--manifest',type=Path)
 p.add_argument('--source-profile',choices=['userdata-pristine','stock-system']);p.add_argument('--source-receipt',type=Path);p.add_argument('--image-index',type=int);p.add_argument('--image',type=Path);p.add_argument('--image-sha256')
 p.add_argument('--inverse-from-image-index',type=int);p.add_argument('--stop-after-chunks',type=int)
 p.add_argument('--part',type=int,choices=[9,10,25,26]);p.add_argument('--chunk',type=int);p.add_argument('--output',type=Path)
 p.add_argument('--evidence',type=Path);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:
  print(json.dumps({'mode':'PLAN_ONLY','operation':a.operation,'automatic_retry':False,'target_command':'rescue-v1','transport':'explicit current transport ID; shell_v2; -T'}));return
 # Budget policy is independently reviewed at this caller boundary, not added
 # to the immutable contract, manifest, source profiles or protocol bytes.
 if not a.io_budgets:raise ValueError('explicit reviewed parent I/O budgets required')
 with a.io_budgets.open('rb') as policy_file:policy=policy_file.read(8193)
 if len(policy)>8192 or hashlib.sha256(policy).hexdigest()!=a.io_budgets_sha256:raise ValueError('budget policy pin')
 policy=json.loads(policy)
 if type(policy) is not dict or set(policy)!={'phases','host_child_cleanup_seconds'}:raise ValueError('budget policy fields')
 budgets=Budgets(policy['phases']);cleanup=positive(policy['host_child_cleanup_seconds'])
 if not a.adb or not a.adb.is_absolute() or hashlib.sha256(a.adb.read_bytes()).hexdigest()!=a.adb_sha256:raise ValueError('explicit hash-pinned ADB binary required')
 if a.transport_id is None or a.transport_id<=0 or not a.evidence:raise ValueError('positive current transport ID and new evidence required')
 b=None;contract=None;prepared=None
 if a.operation in ('write','reconcile'):
  cb=a.contract.read_bytes()
  if hashlib.sha256(cb).hexdigest()!=a.contract_sha256:raise ValueError('reviewed session contract hash required')
  contract=json.loads(cb)
  if type(contract) is not dict or any(type(contract.get(k)) is not str for k in ('mode','manifest_sha256','p10_full_sha256')):raise ValueError('session contract field types')
  if contract['mode']!='PARENT_APPROVED' or contract['armed'] is not True:raise ValueError('parent-approved armed session contract required')
  b=a.manifest.read_bytes()
  if hashlib.sha256(b).hexdigest()!=contract['manifest_sha256']:raise ValueError('manifest pin')
  if len(bytes.fromhex(contract['p10_full_sha256']))!=32:raise ValueError('p10 pin')
  if a.operation=='write':
   if bool(a.source_profile)==bool(a.image):raise ValueError('choose one fixed remote profile or local stock path')
   phase=budgets.start('source_preflight')
   source=RemoteSource(a.source_profile,phase,cleanup_seconds=cleanup) if a.source_profile else local_source(a.image,phase,cleanup_seconds=cleanup)
   stack.callback(source.close)
   source.open()
   prepared=client.prepare_source(b,a.image_index,source,a.image_sha256,a.stop_after_chunks)
   if a.source_receipt:
    if not a.source_profile:raise ValueError('SOURCE receipt is remote only')
    with a.source_receipt.open('x') as receipt:write_all(receipt,json.dumps(source.receipt(),indent=2));receipt.flush();os.fsync(receipt.fileno())
   source.complete_phase()  # Includes optional receipt flush/fsync/close.
 # Full preflight, including optional SOURCE receipt, completes before features.
 fd=None;evidence=None;identity=None
 try:
  control=budgets.start('control')
  cmd=[str(a.adb),'-t',str(a.transport_id)]
  features=features_owned(cmd,control,cleanup)
  control.check()
  if 'shell_v2' not in features:raise ValueError('authenticated endpoint must advertise shell_v2')
  errpath=a.evidence.with_suffix(a.evidence.suffix+'.stderr')
  with a.evidence.open('x') as raw_evidence,ExitStack() as stderr_scope:
   evidence=BoundedJournal(raw_evidence)
   info=os.fstat(evidence.fileno());identity=(info.st_dev,info.st_ino)
   err=stderr_scope.enter_context(errpath.open('xb'))
   evidence.write(json.dumps({'command':cmd+['shell','-T','rescue-v1'],'automatic_retry':False,'contract_sha256':a.contract_sha256})+'\n');evidence.flush();os.fsync(evidence.fileno())
   control.check()
   proc=subprocess.Popen(cmd+['shell','-T','rescue-v1'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
   try:
    try:
     fd=PipeSession(proc.stdout.fileno(),proc.stdin.fileno(),control,stderr=proc.stderr.fileno(),process=proc)
     if a.operation=='status':
      text=client.status(fd);print(text);evidence.write(json.dumps({'status':text})+'\n')
     elif a.operation=='reconcile':
      fd.complete_phase();fd.set_phase(budgets.start('reconciliation'))
      _,same,row=client.reconcile(fd,b,bytes.fromhex(contract['p10_full_sha256']),a.image_index,a.inverse_from_image_index)
      result={'idle_proven':True,'matching_chunks':sum(same),'total_chunks':row['count'],'write_authorized':False};print(json.dumps(result));evidence.write(json.dumps(result)+'\n')
     elif a.operation=='readback':
      if a.part is None or a.chunk is None or not 0<=a.chunk<2**32 or not a.output:raise ValueError('fixed partition/chunk/new output required')
      import struct
      client.send(fd,6,struct.pack('<II',a.part,a.chunk));digest=client.receive(fd,0x86,final=False);data=client.receive(fd,0x87)
      if hashlib.sha256(data).digest()!=digest:raise ValueError('readback transport hash')
      with a.output.open('xb') as out:write_all(out,data);out.flush();os.fsync(out.fileno())
      if hashlib.sha256(a.output.read_bytes()).digest()!=digest:raise ValueError('destination reread failed')
      fd.check()
      result={'chunk_sha256':digest.hex(),'bytes':len(data),'whole_backup_claim':False};print(json.dumps(result));evidence.write(json.dumps(result)+'\n')
     else:
      client.write_image(fd,b,bytes.fromhex(contract['p10_full_sha256']),a.image_index,source,a.image_sha256,evidence,a.inverse_from_image_index,a.stop_after_chunks,prepared=prepared,budgets=budgets,finalize=False)
     proc.stdin.close();fd.read_stream_end(0);fd.check();proc.wait(timeout=max(0.000001,fd.phase.deadline-time.monotonic()));fd.check()
     if proc.returncode:raise RuntimeError('ADB shell endpoint exit='+str(proc.returncode)+'; inspect evidence; do not retry automatically')
    finally:
     # Every source/target host cleanup and stderr publication is inside the
     # UNKNOWN handler, including exceptions raised by these finally blocks.
     try:stack.close()
     finally:
      try:
       if fd is not None:write_all(err,fd.stderr_tail)
       err.flush();os.fsync(err.fileno());err.close()
      finally:reap_owned(proc,cleanup)
    stderr_scope.close()
    fd.check()
    client.publish_success(fd,evidence)
   except BaseException:
    if fd is not None:record_terminal_unknown(fd,evidence,a.evidence,identity)
    raise
  # File-context closure is required publication work too. Nothing can publish
  # successful in-memory completion until it and the final deadline check pass.
  fd.complete_phase();fd.close();fd.phase.check()
  fd.outcome='VERIFIED_COMMIT_RECEIPT' if fd.commit_receipt is not None else 'SUCCESS'
 except BaseException:
  if fd is not None:record_terminal_unknown(fd,evidence,a.evidence,identity)
  raise
 finally:
  if fd is not None and not fd.closed:
   try:fd.close()
   except BaseException:
    record_terminal_unknown(fd,evidence,a.evidence,identity);raise
def main():
 with ExitStack() as stack:run(stack)
if __name__=='__main__':main()
