from pathlib import Path
import struct,os,hashlib,json
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');I=R/'inputs';E=R/'evidence'
class Cow:
 def __init__(self):
  self.base=os.open('/srv/android/asus-radio-trigger-build-r4/system-partition.raw',os.O_RDONLY|os.O_NOFOLLOW);self.fd=os.open(I/'system.qcow2',os.O_RDWR);hdr=os.pread(self.fd,72,0);f=struct.unpack('>IIQIIQIIQQIIQ',hdr);assert f[0]==0x514649fb and f[1]==2;self.c=1<<f[4];self.l1off=f[8];self.mask=((1<<56)-1)&~(self.c-1)
 def addr(self,o):
  cluster=o//self.c;l1=cluster//(self.c//8);l2=cluster%(self.c//8);v=struct.unpack('>Q',os.pread(self.fd,8,self.l1off+8*l1))[0]&self.mask
  if not v:return None
  v=struct.unpack('>Q',os.pread(self.fd,8,v+8*l2))[0];assert not v&(1<<62),'compressed cluster unexpected'
  return (v&self.mask)+(o%self.c) if v&self.mask else None
 def read(self,o,n):
  out=b''
  while n:
   take=min(n,self.c-o%self.c);p=self.addr(o);b=os.pread(self.fd,take,p) if p is not None else os.pread(self.base,take,o);assert len(b)==take;out+=b;o+=take;n-=take
  return out
 def write(self,o,b):
  while b:
   take=min(len(b),self.c-o%self.c);p=self.addr(o);assert p is not None,'offline write requires already allocated metadata cluster';assert os.pwrite(self.fd,b[:take],p)==take;o+=take;b=b[take:]
C=Cow();sb=C.read(1024,1024);assert struct.unpack_from('<H',sb,56)[0]==0xef53;bs=1024<<struct.unpack_from('<I',sb,24)[0];ipg=struct.unpack_from('<I',sb,40)[0];isz=struct.unpack_from('<H',sb,88)[0];assert bs==4096 and isz==256;descsize=struct.unpack_from('<H',sb,254)[0] or 32;assert descsize==32
u16=lambda b,o:struct.unpack_from('<H',b,o)[0]
u32=lambda b,o:struct.unpack_from('<I',b,o)[0]
def inode(n):
 g,k=divmod(n-1,ipg);desc=C.read(bs+g*descsize,descsize);off=u32(desc,8)*bs+k*isz;return off,C.read(off,isz)
def extentblocks(ib):
 assert u32(ib,32)&0x80000;ex=ib[40:100];assert u16(ex,0)==0xf30a and u16(ex,6)==0
 out=[]
 for i in range(u16(ex,2)):
  logical,count,hi,lo=struct.unpack_from('<IHHI',ex,12+12*i);assert count<0x8000
  for k in range(count):out.append((logical+k,((hi<<32)|lo)+k))
 return sorted(out)
def contents(n):
 off,ib=inode(n);size=u32(ib,4);out=bytearray(size)
 for logical,block in extentblocks(ib):
  start=logical*bs
  if start<size:out[start:min(start+bs,size)]=C.read(block*bs,min(bs,size-start))
 return bytes(out)
def children(n):
 b=contents(n);off=0;d={}
 while off<len(b):
  ino,sz,nlen,typ=struct.unpack_from('<IHBB',b,off);assert sz>=8 and off+sz<=len(b)
  if ino:d[b[off+8:off+8+nlen].decode()]=ino
  off+=sz
 return d
def lookup(path):
 n=2
 for part in path.strip('/').split('/'):n=children(n)[part]
 return n
def describe(path):
 n=lookup(path);o,b=inode(n);return dict(path=path,inode=n,mode=oct(u16(b,0)),uid=u16(b,2),gid=u16(b,24),bytes=u32(b,4),atime=u32(b,8),ctime=u32(b,12),mtime=u32(b,16),extra_isize=u16(b,128),raw_inline_xattr_hex=b[160:].hex(),sha256=hashlib.sha256(contents(n)).hexdigest())
