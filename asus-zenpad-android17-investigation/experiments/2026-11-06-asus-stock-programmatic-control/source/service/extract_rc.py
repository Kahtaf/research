#!/usr/bin/env python3
"""Offline canonical OEM image reconstruction and bounded ext4 RC extraction.
No filesystem mounts, device access, subprocesses, or network operations.
"""
from pathlib import Path
import hashlib,json,struct,zipfile,zlib
S=Path(__file__).resolve().parents[2];W=S.parent
ZIP=W/'2026-11-05-asus-latest-android-feasibility/downloads/UL-P00A_2-WW-5.3.20.0-user.zip'
OUT=S/'artifacts/service/oem-system.ext4'
SIZE=3753902080; EXPECT='4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def reconstruct():
 with zipfile.ZipFile(ZIP) as z:
  transfer=z.read('system.transfer.list');lines=transfer.decode().splitlines();assert lines[:4]==['4','765004','0','0']
  with OUT.open('xb') as f,z.open('system.new.dat') as data:
   f.truncate(SIZE);ranges=[]
   for line in lines[4:]:
    cmd,encoded=line.split();numbers=list(map(int,encoded.split(',')));assert numbers[0]==len(numbers)-1 and len(numbers)%2==1
    assert cmd in ('new','zero','erase')
    for i in range(1,len(numbers),2):
     a,b=numbers[i:i+2];assert 0<=a<b<=SIZE//4096;ranges.append((a,b,cmd))
     if cmd=='new':
      f.seek(a*4096);left=(b-a)*4096
      while left:
       chunk=data.read(min(left,1024*1024));assert chunk;f.write(chunk);left-=len(chunk)
   assert data.read(1)==b''
   ordered=sorted(ranges)
   assert all(a[1]<=b[0] for a,b in zip(ordered,ordered[1:]))
 return hashlib.sha256(transfer).hexdigest()
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

def main():
 transfer=reconstruct() if not OUT.exists() else None
 actual=digest(OUT);assert actual==EXPECT
 ext=Ext4(OUT);files={};rcout=S/'artifacts/service/system-rc';rcout.mkdir(exist_ok=True)
 for folder in ['etc/init','vendor/etc/init','odm/etc/init']:
  try:ino=ext.lookup(folder)
  except KeyError:continue
  for name,(n,typ) in ext.directory(ino).items():
   if name.endswith('.rc'):
    assert typ==1;value=ext.content(n);dest=rcout/(folder.replace('/','_')+'__'+name)
    dest.write_bytes(value);files['/system/'+folder+'/'+name]={'sha256':hashlib.sha256(value).hexdigest(),'bytes':len(value),'artifact':str(dest.relative_to(S))}
 result={'zip':str(ZIP),'zip_sha256':digest(ZIP),'system_sha256':actual,'system_bytes':SIZE,'transfer_sha256':transfer,'files':files,'powerctl_hits':{p:Path(S/r['artifact']).read_text() for p,r in files.items() if 'powerctl' in Path(S/r['artifact']).read_text()}}
 (S/'evidence/service/oem-system-rc.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'canonical_sha256':actual,'rc_files':len(files),'powerctl_files':list(result['powerctl_hits'])}))
if __name__=='__main__':main()
