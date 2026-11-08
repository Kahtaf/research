# Narrow ARM32 reader reused from the completed PropertyMap review.
from pathlib import Path
import struct
class Elf:
 def __init__(self,p):
  if not __debug__:raise ValueError('run without Python -O')
  self.d=p if isinstance(p,bytes) else p.read_bytes();d=self.d;assert d[:6]==b'\x7fELF\x01\x01'
  self.e=struct.unpack_from('<HHIIIIIHHHHHH',d,16);assert self.e[0:2]==(3,40)
  self.ph=[struct.unpack_from('<8I',d,self.e[4]+i*self.e[8]) for i in range(self.e[9])]
  self.sh=[struct.unpack_from('<10I',d,self.e[5]+i*self.e[10]) for i in range(self.e[11])]
  names=self.body(self.sh[self.e[12]])
  self.names=[self.z(names,h[0]) for h in self.sh];self.sections=dict(zip(self.names,self.sh))
  for h in self.ph:
   assert h[1]+h[4]<=len(d);assert h[4]<=h[5];assert h[7] in [0,1] or h[1]%h[7]==h[2]%h[7]
  for h in self.sh:
   if h[1]!=8:assert h[4]+h[5]<=len(d)
   if h[2]&2 and h[5] and h[1]!=8:
    matches=[p for p in self.ph if p[0]==1 and p[2]<=h[3] and h[3]+h[5]<=p[2]+p[4] and p[1]+h[3]-p[2]==h[4]]
    assert matches,(self.z(names,h[0]),'not LOAD mapped')
  self.dyn=[struct.unpack_from('<iI',self.body(self.sections['.dynamic']),i) for i in range(0,self.sections['.dynamic'][5],8)];self.dyn=self.dyn[:next(i for i,v in enumerate(self.dyn) if v[0]==0)+1];self.tags=dict(self.dyn)
  for tag,name in [(5,'.dynstr'),(6,'.dynsym'),(0x6ffffef5,'.gnu.hash'),(0x6000000f,'.rel.dyn'),(23,'.rel.plt'),(0x6ffffff0,'.gnu.version'),(0x6ffffffe,'.gnu.version_r'),(0x6ffffffc,'.gnu.version_d')]:
   if tag in self.tags:assert self.tags[tag]==self.sections[name][3],(tag,name)
  strings=self.body(self.sections['.dynstr']);self.strings=strings
  h=self.sections['.dynsym'];b=self.body(h);assert h[6]==self.names.index('.dynstr')
  self.syms=[]
  for i in range(0,len(b),16):
   x=struct.unpack_from('<IIIBBH',b,i);self.syms.append((self.z(strings,x[0]),x[1],x[2],x[3],x[4],self.names[x[5]] if 0<x[5]<len(self.names) else x[5]))
  self.needed=[self.z(strings,v) for k,v in self.dyn if k==1]
 def body(self,h):return self.d[h[4]:h[4]+h[5]]
 @staticmethod
 def z(b,i):assert i<len(b);return b[i:b.index(0,i)].decode()
 def rel(self):
  out=[]
  for name in ['.rel.plt','.rel.dyn']:
   if name in self.sections and self.sections[name][1]==9:
    b=self.body(self.sections[name]);out.extend(struct.unpack_from('<II',b,i) for i in range(0,len(b),8))
  if '.rel.dyn' in self.sections and self.sections['.rel.dyn'][1]==0x60000001:
   b=self.body(self.sections['.rel.dyn']);assert b[:4]==b'APS2';pos=4
   def sleb():
    nonlocal pos
    v=shift=0
    while True:
     c=b[pos];pos+=1;v|=(c&127)<<shift;shift+=7
     if not c&128:return v-(1<<shift) if c&64 else v
   count=sleb();offset=sleb()
   while count:
    n=sleb();flags=sleb();assert 0<n<=count and not flags&12
    delta=sleb() if flags&2 else None;info=sleb() if flags&1 else None
    for _ in range(n):
     offset+=delta if flags&2 else sleb();x=info if flags&1 else sleb();out.append((offset,x))
    count-=n
   assert not any(b[pos:])
  return out
 def hashcheck(self):
  b=self.body(self.sections['.gnu.hash']);nb,first,nw,shift=struct.unpack_from('<4I',b);bloom=struct.unpack_from('<'+'I'*nw,b,16);buckets=struct.unpack_from('<'+'I'*nb,b,16+4*nw);chains=struct.unpack_from('<'+'I'*((len(b)-16-4*nw-4*nb)//4),b,16+4*nw+4*nb)
  def gh(n):
   h=5381
   for c in n.encode():h=(h*33+c)&0xffffffff
   return h
  count=0
  for idx,sym in enumerate(self.syms[first:],first):
   name=sym[0];h=gh(name);assert bloom[(h//32)%nw] & ((1<<(h%32))|(1<<((h>>shift)%32))) == ((1<<(h%32))|(1<<((h>>shift)%32)))
   j=buckets[h%nb];found=False
   while j>=first and j<len(self.syms):
    ch=chains[j-first]
    if ch|1==h|1 and self.syms[j][0]==name:found=True;break
    if ch&1:break
    j+=1
   assert found,(name,idx);count+=1
  return count
