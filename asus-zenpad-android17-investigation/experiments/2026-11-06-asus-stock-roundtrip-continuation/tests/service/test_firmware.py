#!/usr/bin/env python3
"""Actual saved stock ELF routine execution with declared libc/OS stubs.
No Linux, ADB server, device, socket or subprocess is launched by these tests.
"""
from pathlib import Path
import sys,json,struct,hashlib,traceback
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.arm64_const import *
S=Path(__file__).resolve().parents[2];sys.path.insert(0,str(S/'source/service'))
PRIOR=S.parent/'2026-11-06-asus-stock-programmatic-control'
sys.path.insert(0,str(PRIOR/'source/service'))
from elfaudit import ELF

def isolation(event,args):
 if event.startswith(('socket.','subprocess.','os.spawn','os.exec','os.posix_spawn')) or event=='os.system':raise RuntimeError('offline test blocked '+event)
sys.addaudithook(isolation)
X=[UC_ARM64_REG_X0+i for i in range(29)]+[UC_ARM64_REG_X29,UC_ARM64_REG_X30]
class Run:
 def __init__(self,name):
  self.name=name;self.elf=ELF(PRIOR/'artifacts/service'/('boot-init' if name=='init' else 'boot-sbin_adbd'))
  expected={'init':'e9594c0d1cbe7d05d34acd63e90b424672360ceb09112fa16b5b23390c21b7e5','adbd':'78a7adbda0a28da4055da1ea68a2ead8ee01764a365778930ef03e6649dcb450'}
  assert hashlib.sha256(self.elf.data).hexdigest()==expected[name]
  self.u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);self.u.mem_map(0x400000,0x200000);self.u.mem_map(0x700000,0x100000)
  for t,f,o,v,pa,fs,ms,al in self.elf.ph:
   if t==1:self.u.mem_write(v,self.elf.data[o:o+fs])
  self.u.reg_write(UC_ARM64_REG_SP,0x7f0000);self.u.reg_write(UC_ARM64_REG_X30,0x7ff000)
  self.hooks={};self.ranges=[];self.events=[];self.visited=set();self.stop=None
  self.u.hook_add(UC_HOOK_CODE,self.code);self.u.hook_add(UC_HOOK_INTR,self.intr)
 def r(self,i):return self.u.reg_read(X[i])
 def w(self,i,v):self.u.reg_write(X[i],v&((1<<64)-1))
 def text(self,p):
  out=bytearray()
  for i in range(4096):
   b=self.u.mem_read(p+i,1)
   if b==b'\0':return bytes(out).decode()
   out+=b
  raise AssertionError('not terminated')
 def put(self,p,s):self.u.mem_write(p,s.encode()+b'\0')
 def ret(self,v=0):self.w(0,v);self.u.reg_write(UC_ARM64_REG_PC,self.r(30))
 def code(self,u,pc,size,user):
  self.visited.add(pc)
  if pc==0x7ff000:self.stop='returned';u.emu_stop();return
  if pc in self.hooks:self.hooks[pc]();return
  assert any(a<=pc<b for a,b in self.ranges),f'{self.name}: unexpected code path {pc:x}'
 def intr(self,u,n,user):
  nr=self.r(8);args=[self.r(i) for i in range(6)]
  self.events.append(dict(syscall=nr,args=args))
  if nr==81:self.w(0,0);return
  if nr==142:
   assert args[:3]==[0xfee1dead,672274793,0xa1b2c3d4] and self.text(args[3])=='recovery'
   self.events[-1]['literal']='recovery';self.stop='init_RESTART2_syscall_boundary';u.emu_stop();return
  raise AssertionError('unexpected syscall '+str(nr))
 def cmp(self,limited=False):
  a,b=self.text(self.r(0)),self.text(self.r(1))
  if limited:a,b=a[:self.r(2)],b[:self.r(2)]
  self.ret((a>b)-(a<b))
 def memset(self):
  a,b,n=self.r(0),self.r(1),self.r(2);assert n<4096;self.u.mem_write(a,bytes([b&255])*n);self.ret(a)
 def strcpy(self):
  a=self.r(0);b=self.text(self.r(1));n=self.r(2);self.u.mem_write(a,b.encode()[:n-1]+b'\0');self.ret(len(b))
 def length(self):self.ret(len(self.text(self.r(0))))
 def run(self,start):self.u.emu_start(start,0,count=100000);assert self.stop is not None;return self
 def summary(self):return dict(binary=self.name,stop=self.stop,events=self.events,executed_unique_instructions=len(self.visited),stub_entries=[hex(x) for x in sorted(self.visited & self.hooks.keys())])

def adbd(connect_failure=False,send_short=False,target='recovery'):
 r=Run('adbd');r.ranges=[(0x401948,0x401d40),(0x440d30,0x440d34),(0x490130,0x490420),(0x49e218,0x49e230)]
 r.w(0,7);r.w(1,0x701000);r.put(0x701000,target);r.u.mem_write(0x703000,struct.pack('<I',13))
 def fmt():
  assert r.text(r.r(4))=='reboot,%s' and r.r(1)==92
  s='reboot,'+r.text(r.r(5));r.put(r.r(0),s);r.ret(len(s))
 def sock():
  assert [r.r(i) for i in range(3)]==[1,0x80001,0]
  r.events.append(dict(stub='AF_UNIX_socket'));r.ret(20)
 def connect():
  data=bytes(r.u.mem_read(r.r(1),r.r(2)));assert data==struct.pack('<H',1)+b'/dev/socket/property_service\0'
  r.events.append(dict(stub='connect',path='/dev/socket/property_service',failed=connect_failure));r.ret(-1 if connect_failure else 0)
 def send():
  assert r.r(0)==20 and r.r(2)==128
  b=bytes(r.u.mem_read(r.r(1),128));assert struct.unpack_from('<I',b)[0]==1
  name=b[4:36].split(b'\0')[0].decode();value=b[36:].split(b'\0')[0].decode()
  assert (name,value)==('sys.powerctl','reboot,recovery')
  r.events.append(dict(stub='property_send',name=name,value=value,bytes=128,short=send_short));r.ret(127 if send_short else 128)
 def pause():r.stop='adbd_waits_for_reboot_after_property_send';r.u.emu_stop()
 def sideload():r.stop='sideload_cache_branch_NOT_SELECTED_FOR_RECOVERY';r.u.emu_stop()
 r.hooks={0x48a3c4:r.cmp,0x4a42bc:fmt,0x4a40c0:r.length,0x48a240:r.memset,0x4a409c:r.strcpy,
  0x48e214:sock,0x48b3c4:connect,0x4a7344:send,0x4a3f68:lambda:r.ret(1),0x48b384:lambda:r.ret(),
  0x48b5d8:lambda:r.ret(0x703000),0x48cc74:lambda:r.ret(),0x40d760:lambda:r.ret(),0x4a6240:lambda:r.ret(),
  0x48d94c:pause,0x49df60:lambda:r.ret(0),0x4019dc:sideload}
 r.run(0x401948)
 if target=='recovery':assert not (set(range(0x4019c0,0x401bd8,4)) & r.visited)
 return r

def init_property():
 r=Run('init');r.ranges=[(0x410d54,0x411148)]
 r.put(0x701000,'sys.powerctl');r.put(0x701100,'reboot,recovery');r.w(0,0x701000);r.w(1,0x701100)
 def update():
  name,value=r.text(r.r(0)),r.text(r.r(2));assert (name,value)==('sys.powerctl','reboot,recovery')
  r.events.append(dict(stub='add_volatile_property',name=name,value=value));r.ret()
 def notify():
  assert r.text(r.r(0))=='sys.powerctl' and r.text(r.r(1))=='reboot,recovery'
  r.events.append(dict(stub='property_changed_action_queue',name=r.text(r.r(0)),value=r.text(r.r(1))));r.ret()
 r.hooks={0x4c19f8:r.length,0x4a8204:r.cmp,0x4a841c:lambda:r.cmp(True),0x4addf4:lambda:r.ret(0),
          0x4ae1d4:update,0x40b380:notify,0x4194c4:lambda:r.ret()}
 r.run(0x410d54)
 assert all(not x.get('syscall') for x in r.events)
 return r

def init_reboot(sysrq_denied=False):
 r=Run('init');r.ranges=[(0x4077f8,0x407b34),(0x42d448,0x42d9c8),(0x4a8c8c,0x4a8cbc),(0x4bba18,0x4bba30)]
 def small(p,s):assert len(s)<23;r.u.mem_write(p,bytes([len(s)*2])+s.encode()+bytes(23-len(s)))
 small(0x701000,'powerctl');small(0x701018,'reboot,recovery');r.u.mem_write(0x701100,struct.pack('<QQQ',0x701000,0x701030,0x701030));r.w(0,0x701100)
 r.u.mem_write(0x703000,struct.pack('<I',13 if sysrq_denied else 0))
 def getprop():
  assert r.text(r.r(0))=='ro.build.shutdown_timeout';small(r.r(8),'0');r.events.append(dict(stub='getprop',name='ro.build.shutdown_timeout',value='0'));r.ret()
 def number():
  s=r.text(r.r(0));assert s=='0';r.u.mem_write(r.r(1),struct.pack('<Q',r.r(0)+len(s)));r.u.mem_write(0x703000,bytes(4));r.ret(0)
 def fopen():
  assert r.text(r.r(0))=='/proc/mounts' and r.text(r.r(1))=='r';r.events.append(dict(stub='fopen',path='/proc/mounts',mode='r'));r.ret(30)
 def open_():
  assert r.text(r.r(0))=='/proc/sysrq-trigger' and r.r(1)==1
  r.events.append(dict(stub='open',path='/proc/sysrq-trigger',flags=1,denied=sysrq_denied))
  if sysrq_denied:r.u.mem_write(0x703000,struct.pack('<I',13))
  r.ret(-1 if sysrq_denied else 31)
 def write():
  assert r.r(0)==31 and r.r(2)==1 and bytes(r.u.mem_read(r.r(1),1))==b'u'
  r.events.append(dict(stub='write',path='/proc/sysrq-trigger',literal='u'));r.ret(1)
 r.hooks={0x4a8204:r.cmp,0x4a841c:lambda:r.cmp(True),0x410b6c:getprop,0x4a9874:lambda:r.ret(0x703000),
          0x4b92bc:number,0x4abb14:fopen,0x4ab92c:lambda:r.ret(0),0x4abb18:lambda:r.ret(1),
          0x4abb34:open_,0x4c1d6c:write,0x4a9550:lambda:r.ret(),0x42db68:lambda:r.ret(),0x4194c4:lambda:r.ret()}
 r.run(0x4077f8)
 assert r.stop=='init_RESTART2_syscall_boundary'
 assert 0x421f40 not in r.visited and 0x421944 not in r.visited
 return r

def main():
 result={'device_contacted':False,'execution':'Actual extracted stock init/adbd AArch64 instructions with named stubs for pure libc, property socket, shutdown environment, mounts and OS effects. No hardware/runtime proof.','cases':[]}
 try:
  for r in [adbd(),adbd(connect_failure=True),adbd(send_short=True),adbd(target='sideload'),init_property(),init_reboot(),init_reboot(sysrq_denied=True)]:result['cases'].append(r.summary())
  assert result['cases'][0]['stop']=='adbd_waits_for_reboot_after_property_send'
  assert result['cases'][1]['stop']==result['cases'][2]['stop']=='returned'
  result['status']='PASS'
 except BaseException:
  result['status']='FAIL';result['traceback']=traceback.format_exc();raise
 finally:
  p=S/'evidence/service/firmware-emulation.json'
  if p.exists() and json.loads(p.read_text()).get('status')=='FAIL':
   n=1
   while (p.parent/f'failed-firmware-emulation-{n:03}.json').exists():n+=1
   p.rename(p.parent/f'failed-firmware-emulation-{n:03}.json')
  p.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'cases':len(result['cases']),'device_contacted':False}))
if __name__=='__main__':main()
