"""Execute compiled ARM64 client in Unicorn against a virtual AF_UNIX peer.
No socket library, bind/listen/connect on host, device IPC, or block I/O.
Every syscall is intercepted and checked. Fixture ABI follows pinned OEM kernel.
"""
from pathlib import Path
import sys,struct,json,hashlib,resource,gc
S=Path(__file__).resolve().parents[1];ROOT=S.parent
sys.path.insert(0,str(ROOT/'2026-11-06-asus-stock-userdata-recovery/source'))
from elfaudit import ELF
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_INTR
from unicorn.arm64_const import *
resource.setrlimit(resource.RLIMIT_CPU,(45,45))
E=ELF(S/'artifacts/clear-bcb-client');PATH=b'/dev/socket/uncrypt\0';REG=[UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2,UC_ARM64_REG_X3,UC_ARM64_REG_X4,UC_ARM64_REG_X5]
class Fixture:
 def __init__(self,name,expected,opts):
  self.name=name;self.expected=expected;self.opts=opts;self.u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);self.events=[];self.result=None;self.ticks=1000;self.stats=0;self.sends=0;self.receives=0;self.connects=0;self.ack=bytearray();self.rx=bytearray(opts.get('status',bytes.fromhex('00000064')))
  pages=set()
  for typ,flags,off,va,_,sz,memsz,al in E.ph:
   if typ==1:
    for page in range(va&~4095,(va+memsz+4095)&~4095,4096):
     if page not in pages:self.u.mem_map(page,4096);pages.add(page)
    self.u.mem_write(va,E.data[off:off+sz])
  self.u.mem_map(0x700000,0x20000);self.u.hook_add(UC_HOOK_INTR,self.syscall)
 def ret(self,v):self.u.reg_write(REG[0],v&((1<<64)-1))
 def cstr(self,a):return bytes(self.u.mem_read(a,256)).split(b'\0')[0]
 def put32(self,a,x):self.u.mem_write(a,struct.pack('<I',x))
 def syscall(self,u,number,_):
  assert number==2
  n=u.reg_read(UC_ARM64_REG_X8);a,b,c,d,e,f=[u.reg_read(r) for r in REG];o=self.opts
  self.events.append({'nr':n})
  if n==94:self.result=a;u.emu_stop();return
  if n==79:
   assert a==2**64-100 and self.cstr(b)==PATH[:-1] and d==0x100
   self.stats+=1
   if o.get('stat_fail'):self.ret(-13);return
   buf=bytearray(128);struct.pack_into('<QQIIII',buf,0,1,22+(1 if self.stats==2 and o.get('changed_inode') else 0),o.get('mode',0o140600),1,o.get('uid',1000),o.get('gid',1000));u.mem_write(c,bytes(buf));self.ret(0)
  elif n==198:
   assert (a,b,c)==(1,1|0x800|0x80000,0);self.ret(-13 if o.get('socket_fail') else 41)
  elif n==113:
   assert a==1
   if o.get('clock_fail'):self.ret(-1);return
   self.ticks+=1;u.mem_write(b,struct.pack('<qq',self.ticks//1000,self.ticks%1000*1000000));self.ret(0)
  elif n==203:
   self.connects+=1;assert self.connects==1 and a==41 and c==2+len(PATH) and bytes(u.mem_read(b,c))==b'\x01\0'+PATH
   self.ret(o.get('connect_result',0))
  elif n==73:
   assert b==1 and d==e==0
   fd,events,_=struct.unpack('<ihh',u.mem_read(a,8));assert fd==41 and events in (1,4)
   seconds,nanos=struct.unpack('<qq',u.mem_read(c,16));assert 0<=seconds<=10 and 0<=nanos<10**9
   if o.get('poll_eintr_forever'):self.ticks+=1000;self.ret(-4)
   elif o.get('poll_timeout'):self.ticks+=seconds*1000+nanos//1000000;self.ret(0)
   else:u.mem_write(a,struct.pack('<ihh',41,events,events));self.ret(1)
  elif n==209:
   assert a==41 and b==1
   if c==4:u.mem_write(d,struct.pack('<i',o.get('connect_error',0)));self.put32(e,4)
   elif c==17:u.mem_write(d,struct.pack('<iII',o.get('peer_pid',321),o.get('peer_uid',0),o.get('peer_gid',0)));self.put32(e,o.get('cred_len',12))
   else:raise AssertionError(('sockopt',c))
   self.ret(-1 if o.get('sockopt_fail') else 0)
  elif n==205:
   assert a==41
   name=b'/dev/socket/wrong\0' if o.get('bad_path') else PATH
   u.mem_write(b,struct.pack('<H',o.get('family',1))+name);self.put32(c,2+len(name));self.ret(-1 if o.get('name_fail') else 0)
  elif n==207:
   assert a==41 and d==0x40 and e==f==0;self.receives+=1
   if o.get('read_eintr') and self.receives==1:self.ret(-4);return
   if o.get('read_wait') and self.receives==1:self.ret(-11);return
   if o.get('read_timeout') and not self.ack:self.ret(-11);return
   if o.get('read_fail') and not self.ack:self.ret(-5);return
   if o.get('eof_timeout') and self.ack:self.ret(-11);return
   if o.get('extra_byte') and self.ack:u.mem_write(b,b'X');self.ret(1);return
   count=min(c,len(self.rx),o.get('read_chunk',4))
   if count:u.mem_write(b,bytes(self.rx[:count]));del self.rx[:count]
   self.ret(count)
  elif n==206:
   assert a==41 and d==0x4040 and e==f==0 and not self.rx;self.sends+=1
   if o.get('ack_fail'):self.ret(-32);return
   if o.get('ack_zero'):self.ret(0);return
   if o.get('ack_eintr') and self.sends==1:self.ret(-4);return
   if o.get('ack_timeout'):self.ret(-11);return
   count=min(c,o.get('ack_chunk',4));data=bytes(u.mem_read(b,count));assert not any(data);self.ack.extend(data);self.ret(count)
  elif n==57:assert a==41;self.ret(-1 if o.get('close_fail') else 0)
  else:raise AssertionError(('unapproved syscall',n))
 def run(self):
  args=[b'clear-bcb-client',self.opts.get('pid_arg',b'321')]
  if self.opts.get('argc_one'):args=args[:1]
  cursor=0x700000;pointers=[]
  for arg in args:self.u.mem_write(cursor,arg+b'\0');pointers.append(cursor);cursor+=128
  stack=0x71f000;self.u.mem_write(stack,struct.pack('<'+'Q'*(len(args)+2),len(args),*pointers,0));self.u.reg_write(UC_ARM64_REG_SP,stack)
  self.u.emu_start(E.entry,0,timeout=1000000,count=200000)
  assert self.result==self.expected,(self.name,self.result,self.events)
  assert self.connects<=1
  if self.expected in (0,20,24,25):assert self.ack==bytes(4)
  if self.expected in (90,91,92,93):assert self.connects==0
  return dict(name=self.name,exit_code=self.result,connect_attempts=self.connects,ack_hex=self.ack.hex(),syscalls=len(self.events),syscall_numbers=sorted({x['nr'] for x in self.events}))
if __name__=='__main__':
 cases=[('success',0,{}),('oem_failure',20,{'status':bytes.fromhex('ffffffff')}),('fragmented_io',0,{'read_chunk':1,'ack_chunk':1}),('read_eintr',0,{'read_eintr':True}),('ack_eintr',0,{'ack_eintr':True}),('read_wait',0,{'read_wait':True}),('connect_inprogress',0,{'connect_result':-115}),('connect_timeout',94,{'connect_result':-115,'poll_timeout':True}),('connect_error',94,{'connect_result':-115,'connect_error':111}),('connect_eintr_no_retry',94,{'connect_result':-4}),('connect_eagain_no_retry',94,{'connect_result':-11}),('missing_socket',91,{'stat_fail':True}),('socket_mode',91,{'mode':0o140666}),('socket_symlink',91,{'mode':0o120600}),('socket_owner',91,{'uid':0}),('socket_group',91,{'gid':0}),('socket_denied',92,{'socket_fail':True}),('clock_fail',93,{'clock_fail':True}),('changed_inode',95,{'changed_inode':True}),('wrong_pid',96,{'peer_pid':322}),('wrong_uid',96,{'peer_uid':1000}),('wrong_gid',96,{'peer_gid':1000}),('short_credentials',96,{'cred_len':8}),('wrong_name',97,{'bad_path':True}),('wrong_family',97,{'family':0}),('name_failed',97,{'name_fail':True}),('short_status',21,{'status':b'\0\0'}),('little_endian_rejected',22,{'status':bytes.fromhex('64000000')}),('progress_rejected',22,{'status':bytes.fromhex('00000001')}),('read_failure',21,{'read_fail':True}),('read_timeout',21,{'read_timeout':True,'poll_timeout':True}),('read_interrupt_budget',21,{'read_timeout':True,'poll_eintr_forever':True}),('ack_failure',23,{'ack_fail':True}),('ack_zero',23,{'ack_zero':True}),('ack_timeout',23,{'ack_timeout':True,'poll_timeout':True}),('eof_timeout',24,{'eof_timeout':True,'poll_timeout':True}),('extra_after_status',24,{'extra_byte':True}),('close_failure',25,{'close_fail':True}),('no_pid',90,{'argc_one':True}),('bad_pid',90,{'pid_arg':b'321;id'}),('zero_pid',90,{'pid_arg':b'0'}),('init_pid_rejected',90,{'pid_arg':b'1'}),('long_pid',90,{'pid_arg':b'123456789'}),('large_pid',90,{'pid_arg':b'4194305'})]
 results=[]
 for name,expected,opts in cases:
  results.append(Fixture(name,expected,opts).run());gc.collect();assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<1024**3
 (S/'evidence/client-tests.json').write_text(json.dumps(dict(binary_sha256=hashlib.sha256(E.data).hexdigest(),passed=len(results),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,fixture='Unicorn virtual AF_UNIX; all syscalls stubbed; no host sockets; no device operations',cases=results),indent=2)+'\n')
 (S/'evidence/client-disassembly.txt').write_text(E.listing(E.sections['.text'][3],E.sections['.text'][3]+E.sections['.text'][5]))
 print(json.dumps({'passed':len(results),'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))
