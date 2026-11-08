"""Execute pinned OEM AArch64 slices with Unicorn and synthetic memory only.
Every external operation is intercepted. No emulated syscall reaches the host.
No image, partition, process service, mount, or block device is created/opened.
"""
from pathlib import Path
import struct,json,hashlib,resource
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.arm64_const import *
from elfaudit import ELF
S=Path(__file__).resolve().parents[1]
E=ELF(S/'inputs/recovery__sbin_recovery')
PIN='24e3cca9acc9f59947358cb739b1082c9926181623ad075b3a986eba62f40fc7'
REGS=[UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2,UC_ARM64_REG_X3,UC_ARM64_REG_X4,UC_ARM64_REG_X5]
class Fixture:
 def __init__(self):
  self.u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);self.hooks={};self.events=[]
  self.u.mem_map(0x400000,0x180000);self.u.mem_map(0x700000,0x20000);self.u.mem_map(0x800000,0x20000)
  for typ,flags,off,va,_,sz,memsz,al in E.ph:
   if typ==1:self.u.mem_write(va,E.data[off:off+sz])
  self.u.reg_write(UC_ARM64_REG_SP,0x81f000);self.u.reg_write(UC_ARM64_REG_LR,0x710000)
  self.u.hook_add(UC_HOOK_CODE,self.code);self.u.hook_add(UC_HOOK_INTR,self.interrupt)
  self.hooks[0x4e65fc]=lambda: (_ for _ in ()).throw(AssertionError('stack canary failure'))
 def interrupt(self,*a):raise AssertionError('No system calls permitted')
 def ptr(self,a):return struct.unpack('<Q',self.u.mem_read(a,8))[0]
 def putptr(self,a,v):self.u.mem_write(a,struct.pack('<Q',v))
 def str(self,a):
  if not a:return None
  return bytes(self.u.mem_read(a,2048)).split(b'\0')[0].decode()
 def args(self):return [self.u.reg_read(r) for r in REGS]
 def ret(self,v=0):self.u.reg_write(UC_ARM64_REG_X0,v&((1<<64)-1));self.u.reg_write(UC_ARM64_REG_PC,self.u.reg_read(UC_ARM64_REG_LR))
 def code(self,u,pc,size,_):
  if pc==0x710000:u.emu_stop();return
  if pc in self.hooks:self.hooks[pc]();return
  # Only explicitly selected original instruction ranges may run.
  assert any(a<=pc<b for a,b in self.allowed),hex(pc)
 def call(self,pc,*args):
  for reg,arg in zip(REGS,args):self.u.reg_write(reg,arg)
  self.u.emu_start(pc,0x710004,timeout=1000000,count=30000)
  assert self.u.reg_read(UC_ARM64_REG_PC)==0x710000,'budget exceeded'
  return self.u.reg_read(UC_ARM64_REG_X0)
 def ui(self):
  ui_global=self.ptr(0x562810);self.putptr(ui_global,0x700200);self.putptr(0x700200,0x700300)
  self.putptr(0x700368,0x700000)
  def log():self.events.append({'ui':self.str(self.args()[1])});self.ret()
  self.hooks[0x700000]=log

def wipe_test(confirm,selection,erase_result,nvdata=False):
 f=Fixture();f.allowed=[(0x40d7ec,0x40d988),(0x401a00,0x401a08)];f.ui()
 vt=f.ptr(0x562890)+16
 assert f.ptr(vt+0x48)==f.ptr(vt+0x50)==0x401a00
 f.putptr(0x700100,vt)
 def copy():
  d,s,n,*_=f.args();f.u.mem_write(d,bytes(f.u.mem_read(s,n)));f.ret(d)
 def select():f.events.append({'confirm_selection':selection});f.ret(selection)
 def erase():f.events.append({'erase':f.str(f.args()[0]),'mock_return':erase_result});f.ret(erase_result)
 def volume():
  assert f.str(f.args()[0])=='/nvdata';f.events.append({'lookup':'/nvdata','present':nvdata});f.ret(0x700800 if nvdata else 0)
 def bcb():
  a=f.args();f.events.append({'bcb_command':f.str(a[0]),'bcb_recovery':f.str(a[3])});f.ret()
 def clear():f.events.append({'clear_bcb':True});f.ret()
 def stage():f.events.append({'stage':struct.unpack('<I',f.u.mem_read(f.args()[0],4))[0]});f.ret()
 f.hooks.update({0x4d24c8:copy,0x4044bc:select,0x404088:erase,0x407814:volume,0x40def8:bcb,0x40e034:clear,0x40db7c:stage,0x4e6b38:lambda:f.ret(),0x4dd5d8:lambda:f.ret()})
 result=f.call(0x40d7ec,confirm,0x700100)
 erases=[x['erase'] for x in f.events if 'erase'in x]
 if confirm and selection!=7:assert not erases and result==0
 else:
  assert erases==(['/data','/nvdata','/cache'] if nvdata else ['/data','/cache'])
  assert result==1 and f.events[-1]=={'ui':'Data wipe complete.\n'}
 return dict(name=f'wipe_confirm{confirm}_choice{selection}_erase{erase_result}_nvdata{nvdata}',events=f.events,result=result)

def format_test(discard_fail=False,open_fail=False,size=33554432):
 f=Fixture();f.allowed=[(0x407cb8,0x408244),(0x416618,0x41677c),(0x41b1d0,0x41b370)]
 # Synthetic fstab_rec matches the captured OEM /data entry; fake paths only.
 for a,s in [(0x701000,'/data'),(0x701100,'ext4'),(0x701200,'/fixture/userdata'),(0x701300,'/fixture/metadata')]:f.u.mem_write(a,s.encode()+b'\0')
 for off,val in [(0,0x701200),(8,0x701000),(16,0x701100),(48,0x701300),(64,0)]:f.putptr(0x702000+off,val)
 def cmp():a,b,*_=f.args();f.ret(0 if f.str(a)==f.str(b) else 1)
 def op():
  a=f.args();p=f.str(a[0]);f.events.append({'open':p,'flags':a[1]})
  f.ret(-1 if open_fail else (31 if p=='/fixture/metadata' else 32))
 def st():
  fd,buf,*_=f.args();f.u.mem_write(buf,bytes(128));f.u.mem_write(buf+16,struct.pack('<I',0x6000));f.ret()
 def ioctl():
  fd,cmd,buf,*_=f.args();cmd &= 0xffffffff
  if cmd==0x80081272:f.u.mem_write(buf,struct.pack('<Q',size));f.events.append({'ioctl':'BLKGETSIZE64','result_bytes':size});f.ret()
  else:
   assert cmd in (0x1277,0x127d),hex(cmd)
   start,length=struct.unpack('<QQ',f.u.mem_read(buf,16));f.events.append({'ioctl':hex(cmd),'start':start,'length':length})
   f.ret(-1 if discard_fail else 0)
 def rd():
  fd,buf,n,*_=f.args();f.u.mem_write(buf,b'1\n');f.ret(2)
 def mkfs():
  a=f.args();f.events.append({'make_ext4fs_directory':f.str(a[0]),'length':a[1],'mountpoint':f.str(a[2]),'directory':f.str(a[4])});f.ret()
 f.hooks.update({0x4dc760:lambda:f.ret(1),0x4dd870:lambda:f.ret(),0x45098c:lambda:f.ret(0x702000),0x4d2b44:cmp,0x407bf4:lambda:f.ret(),0x43b460:lambda:f.ret(1),0x4dcfc4:lambda:f.ret(),0x4d6260:op,0x4e6898:st,0x4d4500:ioctl,0x4d3fcc:lambda:f.ret(),0x4ecc0c:rd,0x4e3408:lambda:f.ret(1),0x414824:mkfs})
 # get_file_size subtracts the formatter global reserve, initialized zero in fixture (like reset state).
 reserve=f.ptr(0x5628e8);f.putptr(reserve,0)
 result=f.call(0x407cb8,0x701000,0)
 if open_fail:assert result==0xffffffff and not any('make_ext4fs_directory'in x for x in f.events)
 else:
  assert {'ioctl':'0x1277','start':0,'length':size} in f.events
  assert result==0 and f.events[-1]['make_ext4fs_directory']=='/fixture/userdata'
 return dict(name=f'format_discardfail{discard_fail}_openfail{open_fail}_size{size}',events=f.events,result=result)

def formatter_defaults_test(size):
 f=Fixture();f.allowed=[(0x413cbc,0x413e6c)]
 f.u.reg_write(UC_ARM64_REG_X28,0x702000);f.u.reg_write(UC_ARM64_REG_X29,0x81e000)
 f.hooks[0x413e6c]=lambda:f.ret()
 f.call(0x413cbc,size)
 b=bytes(f.u.mem_read(0x702000,64))
 length=struct.unpack_from('<Q',b,0)[0]
 block_size,blocks_per_group,inodes_per_group,inode_size,inodes,journal_blocks=struct.unpack_from('<6I',b,8)
 ro,compat,inc=struct.unpack_from('<HHH',b,32)
 assert (length,block_size,inode_size,compat,inc,ro)==(size//4096*4096,4096,256,0x1c,0x42,0x13)
 return dict(name='formatter_defaults_'+str(size),partition_bytes=size,filesystem_bytes=length,block_size=block_size,inode_size=inode_size,blocks_per_group=blocks_per_group,inodes_per_group=inodes_per_group,inodes=inodes,journal_blocks=journal_blocks,compat=hex(compat),incompat=hex(inc),ro_compat=hex(ro),limits='Actual original arithmetic/feature-initialization instructions only; no formatter I/O, filesystem construction or mount executed.')

def menu_key_test():
 f=Fixture();f.allowed=[(0x40192c,0x40194c),(0x401968,0x4019f0)]
 actual={}
 for key in [114,115,116]:
  result=f.call(0x401968,0,key,1);actual[str(key)]=struct.unpack('<i',struct.pack('<I',result&0xffffffff))[0]
 assert actual=={'114':-3,'115':-2,'116':-4},actual
 assert f.call(0x40192c,0,4)==6
 return dict(name='actual_menu_keys_and_dispatch',keycodes_to_action=actual,menu_index4_action=6,limits='Original instruction execution; no input driver or display test.')

def main():
 assert hashlib.sha256(E.data).hexdigest()==PIN
 results=[wipe_test(1,0,1),wipe_test(1,7,1),wipe_test(1,7,0),wipe_test(0,7,0),wipe_test(1,7,1,True),format_test(),format_test(True),format_test(open_fail=True),format_test(size=67108864),formatter_defaults_test(11331268096),formatter_defaults_test(67108864),menu_key_test()]
 out={'recovery_sha256':PIN,'execution':'original AArch64 slices; all external effects mocked; no kernel/crypto/UI/device runtime proof','cases':results,'passed':len(results)}
 (S/'evidence/emulation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'passed':len(results)}))
if __name__=='__main__':main()
