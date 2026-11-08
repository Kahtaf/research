from pathlib import Path
import struct,os,hashlib,json
R=Path('/srv/android/asus-r9-actual-early-runtime-20261106');I=R/'inputs';E=R/'evidence'
class Cow:
 def __init__(self):
  self.base=os.open('/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw',os.O_RDONLY|os.O_NOFOLLOW);self.fd=os.open(I/'system.qcow2',os.O_RDWR);hdr=os.pread(self.fd,72,0);f=struct.unpack('>IIQIIQIIQQIIQ',hdr);assert f[0]==0x514649fb and f[1]==2;self.c=1<<f[4];self.l1off=f[8];self.mask=((1<<56)-1)&~(self.c-1)
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
# Exact existing genuine xattr storage, without asking unloaded SELinux to translate it.
changes=[]
for source,target,expected in [('system/bin/sh','system/bin/actual-runtime-observer',b'u:object_r:shell_exec:s0\0'),('system/etc/init/apexd.rc','system/etc/init/actual-runtime-observer.rc',b'u:object_r:system_file:s0\0')]:
 _,src=inode(lookup(source));off,dst=inode(lookup(target));assert u16(src,128)==32 and u16(dst,128)==32;assert src[160:164]==bytes.fromhex('000002ea') and expected in src[160:];assert dst[160:164] in [b'\0'*4,bytes.fromhex('000002ea')];before=describe(target);C.write(off+160,src[160:]);after=describe(target);assert after['raw_inline_xattr_hex']==src[160:].hex();changes.append(dict(source_xattr_from=source,before=before,after=after))
os.fsync(C.fd)
checks=[]
for path,payload,mode,uid,gid,label in [('system/vendor/etc/fstab.mt8163','vendor.fstab',0o100644,0,0,b'u:object_r:vendor_configs_file:s0\0'),('system/bin/actual-runtime-observer','observer',0o100755,0,2000,b'u:object_r:shell_exec:s0\0'),('system/etc/init/actual-runtime-observer.rc','observer.rc',0o100644,0,0,b'u:object_r:system_file:s0\0')]:
 d=describe(path);assert contents(lookup(path))==(I/payload).read_bytes();assert d['mode']==oct(mode) and d['uid']==uid and d['gid']==gid and label in bytes.fromhex(d['raw_inline_xattr_hex']);checks.append(d)
# Original fstab inline xattrs and uid/gid/mode/atime/mtime are byte-identical to the base.
o,b=inode(lookup('system/vendor/etc/fstab.mt8163'));original=os.pread(C.base,256,o);assert b[160:]==original[160:] and b[:4]==original[:4] and b[24:26]==original[24:26] and b[8:12]==original[8:12] and b[16:20]==original[16:20]
d=dict(passed=True,files_changed=['system/vendor/etc/fstab.mt8163'],files_added=['system/bin/actual-runtime-observer','system/etc/init/actual-runtime-observer.rc'],offline_xattr_changes=changes,checks=checks,fstab_preserved_inode=lookup('system/vendor/etc/fstab.mt8163'),fstab_xattr_uid_gid_mode_atime_mtime_unchanged=True,filesystem_side_effects='ext4 allocations/bitmaps/inode and directory times, directory entries and clean mount superblock metadata; no other file payload edits requested',qcow2_bytes=(I/'system.qcow2').stat().st_size)
(E/'cow-file-verification.json').write_text(json.dumps(d,indent=2));os.chmod(I/'system.qcow2',0o444);print(json.dumps(d,indent=2))
