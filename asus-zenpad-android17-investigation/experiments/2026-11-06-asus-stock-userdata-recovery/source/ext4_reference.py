"""Bounded read-only ext4 reader adapted from stock-programmatic-control extract_rc.py."""
from pathlib import Path
import struct
SIZE=3753902080
class Ext4:
 def __init__(self,p):
  self.f=p.open('rb');s=self.read(1024,1024);assert struct.unpack_from('<H',s,56)[0]==0xef53
  self.bs=1024<<struct.unpack_from('<I',s,24)[0];assert self.bs==4096
  self.ipg=struct.unpack_from('<I',s,40)[0];self.isz=struct.unpack_from('<H',s,88)[0]
  self.ds=max(32,struct.unpack_from('<H',s,254)[0]);assert self.ds in (32,64)
 def read(self,o,n):
  assert 0<=o and 0<=n<=2*1024*1024 and o+n<=SIZE
  self.f.seek(o);b=self.f.read(n);assert len(b)==n;return b
 def inode(self,n):
  assert 1<=n<1000000;g,i=divmod(n-1,self.ipg);d=self.read(self.bs+g*self.ds,self.ds)
  table=struct.unpack_from('<I',d,8)[0]+((struct.unpack_from('<I',d,40)[0]<<32) if self.ds==64 else 0)
  return self.read(table*self.bs+i*self.isz,self.isz)
 def extents(self,raw,depth=None):
  magic,count,maxn,d,_=struct.unpack_from('<HHHHI',raw,0);assert magic==0xf30a and count<=maxn and d<=4
  if depth is not None:assert d==depth
  out=[]
  for i in range(count):
   o=12+i*12
   if d:
    logical,low,high,_=struct.unpack_from('<IIHH',raw,o);out+=self.extents(self.read((low+(high<<32))*self.bs,self.bs),d-1)
   else:
    logical,length,high,low=struct.unpack_from('<IHHI',raw,o);assert length<=32768
    out.append((logical,length,low+(high<<32)))
  return out
 def content(self,n):
  i=self.inode(n);mode=struct.unpack_from('<H',i,0)[0];sz=struct.unpack_from('<I',i,4)[0]+(struct.unpack_from('<I',i,108)[0]<<32)
  assert sz<=1024*1024
  if mode&0xf000==0xa000 and sz<=60:return i[40:40+sz]
  flags=struct.unpack_from('<I',i,32)[0];assert flags&0x80000
  out=bytearray(sz)
  for logical,length,physical in self.extents(i[40:100]):
   a=logical*self.bs;n=min(length*self.bs,sz-a);assert n>=0
   out[a:a+n]=self.read(physical*self.bs,n)
  return bytes(out)
 def directory(self,n):
  assert struct.unpack_from('<H',self.inode(n),0)[0]&0xf000==0x4000
  b=self.content(n);pos=0;out={}
  while pos<len(b):
   ino,rec,namelen,typ=struct.unpack_from('<IHBB',b,pos);assert rec>=8 and pos+rec<=len(b) and namelen<=rec-8
   if ino:
    name=b[pos+8:pos+8+namelen].decode();assert name not in out;out[name]=(ino,typ)
   pos+=rec
  return out
 def lookup(self,path):
  n=2
  for part in path.strip('/').split('/'):
   if not part:continue
   n=self.directory(n)[part][0]
  return n

