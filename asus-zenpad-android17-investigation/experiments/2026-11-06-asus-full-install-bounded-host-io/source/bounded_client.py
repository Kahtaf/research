"""RSC1 host I/O revision; parse/status/reconcile copied byte-for-byte.
Original pinned client remains external evidence and is never monkeypatched.
"""
import hashlib,struct
from pinned import client as legacy
CHUNK=legacy.CHUNK

def send(fd,op,b=b''):
 fd.send(b'RSC1'+struct.pack('<II',op,len(b)),b,mutation=op in (3,4,5,7,9))
def receive(fd,op):
 def decode(h):
  magic,got,n=struct.unpack('<4sII',h)
  if magic!=b'RSC1' or n>CHUNK:raise ValueError('invalid frame')
  return got,n
 got,b=fd.receive(12,decode)
 try:
  if got==255:raise RuntimeError(b.decode(errors='replace'))
  if got!=op:raise ValueError('unexpected opcode')
  return b
 except BaseException:
  fd.poison();raise
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
