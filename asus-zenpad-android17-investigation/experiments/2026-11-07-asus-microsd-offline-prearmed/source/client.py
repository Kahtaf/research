"""Fixed binary client. PLAN ONLY unless --execute is explicit.
Connection is an inherited full-duplex FD, supplied by parent's authenticated shell_v2 non-PTY transport.
This tool does not invoke ADB, choose a device, reboot, or reconnect automatically."""
import argparse,hashlib,json,os,struct,sys
from pathlib import Path
from manifest import CHUNK,digest_file
def readn(fd,n):
 b=bytearray()
 while len(b)<n:
  q=os.read(fd[0] if isinstance(fd,tuple) else fd,n-len(b))
  if not q:raise EOFError('transport lost; mutation uncertain; no automatic retry')
  b+=q
 return bytes(b)
def send(fd,op,b=b''):
 data=b'RSC1'+struct.pack('<II',op,len(b))+b
 while data:
  n=os.write(fd[1] if isinstance(fd,tuple) else fd,data)
  if n<=0:raise IOError('short transport')
  data=data[n:]
def receive(fd,op):
 h=readn(fd,12);magic,got,n=struct.unpack('<4sII',h)
 if magic!=b'RSC1' or n>CHUNK:raise ValueError('invalid frame')
 b=readn(fd,n)
 if got==255:raise RuntimeError(b.decode(errors='replace'))
 if got!=op:raise ValueError('unexpected opcode')
 return b
def parse(b):
 if len(b)<112 or b[:8]!=b'ASUSR002' or struct.unpack_from('<I',b,8)[0]!=2:raise ValueError('manifest')
 rows=[];p=112;n=struct.unpack_from('<I',b,12)[0]
 if n not in (0,2,4,5):raise ValueError('image count')
 for i in range(n):
  role,part,size=struct.unpack_from('<IIQ',b,p);full=b[p+16:p+48];count=struct.unpack_from('<I',b,p+48)[0];p+=52
  chunks=b[p:p+count*32];p+=count*32
  if role!=i or part!=(26 if i==4 else 9 if i%2 else 25) or count!=(size+CHUNK-1)//CHUNK or len(chunks)!=count*32:raise ValueError('record')
  rows.append(dict(size=size,full=full,chunks=chunks,count=count,part=part))
 if p!=len(b):raise ValueError('trailing bytes')
 return rows
def status(fd):
 send(fd,1);return receive(fd,0x81).decode()
def reconcile(fd,b,p10,index,inverse_from=None):
 rows=parse(b)
 if index<0 or index>=len(rows) or len(p10)!=32:raise ValueError('selection')
 payload=hashlib.sha256(b).digest()+p10+struct.pack('<I',index)
 if inverse_from is not None:
  if index>1 or not 0<=inverse_from<len(rows):raise ValueError('explicit original inverse selection')
  payload+=struct.pack('<I',inverse_from)+rows[index]['full']
 send(fd,8 if inverse_from is not None else 2,payload)
 r=receive(fd,0x82);row=rows[index]
 if len(r)!=32+row['count'] or any(v not in (0,1) for v in r[32:]):raise ValueError('reconciliation reply')
 return r[:32],r[32:],row
def prepare_image(b,index,path,reviewed_sha,stop_after=None):
 # Validate complete local raw bytes before requesting any mutation.
 rows=parse(b)
 if index is None or not 0<=index<len(rows):raise ValueError('image index')
 row=rows[index]
 if stop_after is not None and not 1<=stop_after<=row['count']:raise ValueError('bounded positive partial trial chunk count required')
 full,chunks=digest_file(path,row['size'])
 if full!=row['full'] or full.hex()!=reviewed_sha or b''.join(chunks)!=row['chunks']:raise ValueError('raw image does not match reviewed manifest')
 return (hashlib.sha256(b).digest(),index,str(path),reviewed_sha,stop_after)
def write_image(fd,b,p10,index,path,reviewed_sha,evidence,inverse_from=None,stop_after=None,prepared=None):
 expected=(hashlib.sha256(b).digest(),index,str(path),reviewed_sha,stop_after)
 if prepared is None:prepared=prepare_image(b,index,path,reviewed_sha,stop_after)
 if prepared!=expected:raise ValueError('prepared source/selection mismatch')
 evidence.write(json.dumps({'status':status(fd)})+'\n');evidence.flush()
 token,same,row=reconcile(fd,b,p10,index,inverse_from)
 evidence.write(json.dumps({'idle_proven':True,'reconciled_matching_chunks':sum(same),'manifest':hashlib.sha256(b).hexdigest(),'p10':p10.hex(),'image':index,'explicit_inverse_from':inverse_from})+'\n');evidence.flush();os.fsync(evidence.fileno())
 send(fd,3,token);receive(fd,0x83)
 f=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  for i,match in enumerate(same):
   n=min(CHUNK,row['size']-i*CHUNK);data=os.pread(f,n,i*CHUNK)
   if len(data)!=n or hashlib.sha256(data).digest()!=row['chunks'][i*32:i*32+32]:raise ValueError('source changed')
   send(fd,7 if match else 4,b'' if match else data)
   ack=receive(fd,0x84)
   if len(ack)!=8 or struct.unpack('<II',ack)[0]!=i:raise ValueError('ack sequence')
   evidence.write(json.dumps({'chunk':i,'skipped':bool(struct.unpack('<II',ack)[1])})+'\n');evidence.flush()
   if stop_after is not None and i+1==stop_after:
    evidence.write(json.dumps({'partial_trial_stopped':i+1,'whole_partition_verified':False,'reconciliation_required':True})+'\n');evidence.flush();os.fsync(evidence.fileno());return
  send(fd,5);got=receive(fd,0x85)
  if got!=row['full']:raise ValueError('whole readback mismatch')
  send(fd,9,got)
  if receive(fd,0x89)!=got:raise ValueError('commit receipt mismatch')
  evidence.write(json.dumps({'whole_partition_verified':got.hex()})+'\n');evidence.flush();os.fsync(evidence.fileno())
 finally:os.close(f)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['status','readback','reconcile','write']);p.add_argument('--fd',type=int);p.add_argument('--manifest',type=Path);p.add_argument('--manifest-sha256');p.add_argument('--p10-sha256');p.add_argument('--image-index',type=int);p.add_argument('--image',type=Path);p.add_argument('--image-sha256');p.add_argument('--part',type=int,choices=[9,10,25,26]);p.add_argument('--chunk',type=int);p.add_argument('--output',type=Path);p.add_argument('--evidence',type=Path);p.add_argument('--inverse-from-image-index',type=int);p.add_argument('--stop-after-chunks',type=int);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:print(json.dumps({'mode':'PLAN_ONLY','operation':a.operation,'transport':'parent supplied authenticated shell_v2 non-PTY FD','automatic_retry':False}));return
 if a.fd is None:raise ValueError('--fd required')
 if a.operation=='status':print(status(a.fd));return
 if a.operation=='readback':
  if a.part is None or a.chunk is None or not 0<=a.chunk<2**32 or not a.output:raise ValueError('fixed part/chunk/output required')
  send(a.fd,6,struct.pack('<II',a.part,a.chunk));h=receive(a.fd,0x86);b=receive(a.fd,0x87)
  if hashlib.sha256(b).digest()!=h:raise ValueError('transport corruption')
  with a.output.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  if hashlib.sha256(a.output.read_bytes()).digest()!=h:raise ValueError('destination mismatch')
  print(json.dumps({'chunk_sha256':h.hex(),'bytes':len(b),'whole_backup_claim':False}));return
 b=a.manifest.read_bytes()
 if hashlib.sha256(b).hexdigest()!=a.manifest_sha256:raise ValueError('explicit reviewed manifest SHA required')
 p10=bytes.fromhex(a.p10_sha256)
 if a.operation=='reconcile':
  _,same,row=reconcile(a.fd,b,p10,a.image_index,a.inverse_from_image_index);print(json.dumps({'idle_proven':True,'matching_chunks':sum(same),'total_chunks':row['count'],'write_authorized':False}));return
 if not a.evidence or not a.image or not a.image_sha256:raise ValueError('image, reviewed hash, new evidence file required')
 with a.evidence.open('x') as e:write_image(a.fd,b,p10,a.image_index,a.image,a.image_sha256,e,a.inverse_from_image_index,a.stop_after_chunks)
if __name__=='__main__':main()
