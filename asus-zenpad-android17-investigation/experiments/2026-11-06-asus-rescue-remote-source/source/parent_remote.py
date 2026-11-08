"""Parent-only transport adapter. PLAN ONLY by default. Never retries or reboots.
Execute only after parent has selected and reviewed the current authenticated ADB transport."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
import source_client as client
from sources import RemoteSource,local_source
from contextlib import ExitStack
from journal import BoundedJournal,StderrCapture
def run(stack):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('operation',choices=['status','readback','reconcile','write'])
 p.add_argument('--adb',type=Path);p.add_argument('--adb-sha256');p.add_argument('--transport-id',type=int)
 p.add_argument('--contract',type=Path);p.add_argument('--contract-sha256');p.add_argument('--manifest',type=Path)
 p.add_argument('--source-profile',choices=['userdata-pristine','stock-system']);p.add_argument('--source-receipt',type=Path);p.add_argument('--image-index',type=int);p.add_argument('--image',type=Path);p.add_argument('--image-sha256')
 p.add_argument('--inverse-from-image-index',type=int);p.add_argument('--stop-after-chunks',type=int)
 p.add_argument('--part',type=int,choices=[9,10,25,26]);p.add_argument('--chunk',type=int);p.add_argument('--output',type=Path)
 p.add_argument('--evidence',type=Path);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:
  print(json.dumps({'mode':'PLAN_ONLY','operation':a.operation,'automatic_retry':False,'target_command':'rescue-v1','transport':'explicit current transport ID; shell_v2; -T'}));return
 if not a.adb or not a.adb.is_absolute() or hashlib.sha256(a.adb.read_bytes()).hexdigest()!=a.adb_sha256:raise ValueError('explicit hash-pinned ADB binary required')
 if a.transport_id is None or a.transport_id<=0 or not a.evidence:raise ValueError('positive current transport ID and new evidence required')
 b=None;contract=None;prepared=None
 if a.operation in ('write','reconcile'):
  cb=a.contract.read_bytes()
  if hashlib.sha256(cb).hexdigest()!=a.contract_sha256:raise ValueError('reviewed session contract hash required')
  contract=json.loads(cb)
  if contract['mode']!='PARENT_APPROVED' or not contract['armed']:raise ValueError('parent-approved armed session contract required')
  b=a.manifest.read_bytes()
  if hashlib.sha256(b).hexdigest()!=contract['manifest_sha256']:raise ValueError('manifest pin')
  if len(bytes.fromhex(contract['p10_full_sha256']))!=32:raise ValueError('p10 pin')
  if a.operation=='write':
   if bool(a.source_profile)==bool(a.image):raise ValueError('choose one fixed remote profile or local stock path')
   source=RemoteSource(a.source_profile) if a.source_profile else local_source(a.image)
   stack.callback(source.close)
   if a.source_profile:source.open()
   prepared=client.prepare_source(b,a.image_index,source,a.image_sha256,a.stop_after_chunks)
   if a.source_receipt:
    if not a.source_profile:raise ValueError('SOURCE receipt is remote only')
    with a.source_receipt.open('x') as receipt:json.dump(source.receipt(),receipt,indent=2);receipt.flush();os.fsync(receipt.fileno())
 # All expensive local image verification happens before opening the target shell.
 cmd=[str(a.adb),'-t',str(a.transport_id)]
 features=subprocess.run(cmd+['features'],check=True,capture_output=True,text=True,timeout=15).stdout.strip().split(',')
 if 'shell_v2' not in features:raise ValueError('authenticated endpoint must advertise shell_v2')
 errpath=a.evidence.with_suffix(a.evidence.suffix+'.stderr')
 with a.evidence.open('x') as raw_evidence,errpath.open('xb') as err:
  evidence=BoundedJournal(raw_evidence)
  evidence.write(json.dumps({'command':cmd+['shell','-T','rescue-v1'],'automatic_retry':False,'contract_sha256':a.contract_sha256})+'\n');evidence.flush();os.fsync(evidence.fileno())
  proc=subprocess.Popen(cmd+['shell','-T','rescue-v1'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
  stderr_capture=StderrCapture(proc.stderr,err)
  fd=(proc.stdout.fileno(),proc.stdin.fileno())
  try:
   if a.operation=='status':
    text=client.status(fd);print(text);evidence.write(json.dumps({'status':text})+'\n')
   elif a.operation=='reconcile':
    _,same,row=client.reconcile(fd,b,bytes.fromhex(contract['p10_full_sha256']),a.image_index,a.inverse_from_image_index)
    result={'idle_proven':True,'matching_chunks':sum(same),'total_chunks':row['count'],'write_authorized':False};print(json.dumps(result));evidence.write(json.dumps(result)+'\n')
   elif a.operation=='readback':
    if a.part is None or a.chunk is None or not 0<=a.chunk<2**32 or not a.output:raise ValueError('fixed partition/chunk/new output required')
    import struct
    client.send(fd,6,struct.pack('<II',a.part,a.chunk));digest=client.receive(fd,0x86);data=client.receive(fd,0x87)
    if hashlib.sha256(data).digest()!=digest:raise ValueError('readback transport hash')
    with a.output.open('xb') as out:out.write(data);out.flush();os.fsync(out.fileno())
    if hashlib.sha256(a.output.read_bytes()).digest()!=digest:raise ValueError('destination reread failed')
    result={'chunk_sha256':digest.hex(),'bytes':len(data),'whole_backup_claim':False};print(json.dumps(result));evidence.write(json.dumps(result)+'\n')
   else:
    client.write_image(fd,b,bytes.fromhex(contract['p10_full_sha256']),a.image_index,source,a.image_sha256,evidence,a.inverse_from_image_index,a.stop_after_chunks,prepared=prepared)
   proc.stdin.close();proc.wait(timeout=30)
   if proc.returncode:raise RuntimeError('ADB shell endpoint exit='+str(proc.returncode)+'; inspect evidence; do not retry automatically')
   evidence.flush();os.fsync(evidence.fileno())
  except BaseException:
   evidence.write(json.dumps({'outcome':'UNCERTAIN_OR_REFUSED','automatic_retry':False,'next':'prove idle and explicitly reconcile actual chunks; no offset resume'})+'\n');evidence.flush();os.fsync(evidence.fileno())
   if proc.stdin and not proc.stdin.closed:proc.stdin.close()
   if proc.poll() is None:proc.terminate()
   raise
  finally:
   proc.stdout.close()
   if proc.poll() is None:
    try:proc.wait(timeout=5)
    except subprocess.TimeoutExpired:proc.kill();proc.wait()
   stderr_capture.finish()
def main():
 with ExitStack() as stack:run(stack)
if __name__=='__main__':main()
