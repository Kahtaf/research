"""Bounded DEX037 reader; no VM/device execution or decompiler installation."""
from pathlib import Path
import struct
class Dex:
 def __init__(self,p):
  self.path=Path(p);self.b=self.path.read_bytes();assert self.b[:8] in (b'dex\n037\0',b'dex\n035\0');assert self.u32(32)==len(self.b) and self.u32(36)==112 and self.u32(40)==0x12345678
  self.tables={n:(self.u32(o),self.u32(o+4)) for n,o in [('string',56),('type',64),('proto',72),('field',80),('method',88),('class',96)]};self.strings={};self.classes={}
  for i in range(self.tables['class'][0]):
   row=struct.unpack_from('<8I',self.b,self.tables['class'][1]+i*32);self.classes[self.type(row[0])]=row
 def u16(self,p):return struct.unpack_from('<H',self.b,p)[0]
 def u32(self,p):return struct.unpack_from('<I',self.b,p)[0]
 def leb(self,p,signed=False):
  start=p;n=0;shift=0
  while True:
   assert p-start<5;x=self.b[p];p+=1;n|=(x&127)<<shift;shift+=7
   if x<128:break
  if signed and x&64:n-=1<<shift
  return n,p
 def string(self,i):
  assert 0<=i<self.tables['string'][0]
  if i not in self.strings:
   a=self.u32(self.tables['string'][1]+4*i);_,a=self.leb(a);end=self.b.index(0,a);self.strings[i]=self.b[a:end].decode('utf8',errors='replace')
  return self.strings[i]
 def type(self,i):return self.string(self.u32(self.tables['type'][1]+4*i))
 def proto(self,i):
  _,ret,args=struct.unpack_from('<III',self.b,self.tables['proto'][1]+i*12)
  return '('+(''.join(self.type(self.u16(args+4+j*2)) for j in range(self.u32(args))) if args else '')+')'+self.type(ret)
 def field(self,i):
  cl,ty,name=struct.unpack_from('<HHI',self.b,self.tables['field'][1]+i*8);return self.type(cl)+'->'+self.string(name)+':'+self.type(ty)
 def method(self,i):
  cl,pr,name=struct.unpack_from('<HHI',self.b,self.tables['method'][1]+i*8);return self.type(cl)+'->'+self.string(name)+self.proto(pr)
 def value(self,p):
  h=self.b[p];p+=1;kind=h&31;n=(h>>5)+1
  if kind==0x1e:return None,p
  if kind==0x1f:return bool(h>>5),p
  if kind==0x1c:
   count,p=self.leb(p);out=[]
   for _ in range(count):v,p=self.value(p);out.append(v)
   return out,p
  assert kind in (0,2,3,4,6,0x10,0x11,0x15,0x16,0x17,0x18,0x19,0x1a,0x1b),hex(kind)
  raw=self.b[p:p+n];p+=n;x=int.from_bytes(raw,'little',signed=kind in (0,2,4,6))
  if kind==0x17:return self.string(x),p
  if kind==0x18:return self.type(x),p
  return x,p
 def classdata(self,name):
  row=self.classes[name];p=row[6];counts=[]
  for _ in range(4):n,p=self.leb(p);counts.append(n)
  fields=[];methods=[]
  for count,label in zip(counts[:2],['static','instance']):
   idx=0
   for _ in range(count):delta,p=self.leb(p);idx+=delta;access,p=self.leb(p);fields.append(dict(index=idx,name=self.field(idx),access=access,kind=label))
  for count,label in zip(counts[2:],['direct','virtual']):
   idx=0
   for _ in range(count):delta,p=self.leb(p);idx+=delta;access,p=self.leb(p);code,p=self.leb(p);methods.append(dict(index=idx,name=self.method(idx),access=access,code_offset=code,kind=label))
  if row[7]:
   count,p=self.leb(row[7]);assert count<=counts[0]
   for j in range(count):v,p=self.value(p);fields[j]['initial_value']=v
  return dict(name=name,superclass=self.type(row[2]) if row[2]!=0xffffffff else None,access=row[1],class_data_offset=row[6],fields=fields,methods=methods)
 def code(self,off):
  regs,ins,outs,tries,debug,size=struct.unpack_from('<HHHHII',self.b,off)
  units=list(struct.unpack_from('<'+'H'*size,self.b,off+16));result=dict(registers=regs,ins=ins,outs=outs,tries=tries,debug_info_off=debug,insns_size=size,units=units,code_offset=off)
  handlers={};tryitems=[]
  if tries:
   p=off+16+size*2+(2 if size%2 else 0);hstart=p+8*tries;num,q=self.leb(hstart)
   for _ in range(num):
    relative=q-hstart;n,q=self.leb(q,True);pairs=[]
    for j in range(abs(n)):ty,q=self.leb(q);addr,q=self.leb(q);pairs.append([self.type(ty),addr])
    if n<=0:addr,q=self.leb(q);pairs.append(['any',addr])
    handlers[relative]=pairs
   for j in range(tries):start,count,h=struct.unpack_from('<IHH',self.b,p+j*8);tryitems.append(dict(start=start,end=start+count,handlers=handlers[h]))
  result['try_items']=tryitems;return result
