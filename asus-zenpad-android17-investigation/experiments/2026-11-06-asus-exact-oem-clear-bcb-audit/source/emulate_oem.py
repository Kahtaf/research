"""Pinned OEM instructions, virtual memory + stubbed libc/OS. No host/device IPC.
fs_mgr_read_fstab is explicitly stubbed from the public OEM text; actual
fs_mgr_get_entry_for_mount_point instructions resolve /misc. No actual unit bytes.
"""
from pathlib import Path
import sys,struct,json,hashlib,resource
ROOT=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'2026-11-06-asus-stock-userdata-recovery/source'))
from elfaudit import ELF
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.arm64_const import *
resource.setrlimit(resource.RLIMIT_CPU,(45,45))

E=ELF(ROOT/'2026-11-06-asus-pending-recovery-request/source/uncrypt')
PIN='3f7e8c8ed7272540315eaef0af405a57ac701db121dd5c842a8b04be721b2671'
assert hashlib.sha256(E.data).hexdigest()==PIN
FSTAB=(ROOT/'2026-11-06-asus-stock-userdata-recovery/inputs/boot__fstab.mt8163').read_text()
REG=[UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2,UC_ARM64_REG_X3,UC_ARM64_REG_X4,UC_ARM64_REG_X5]
PLT={int(k,16):v for k,v in json.loads((S/'evidence/uncrypt-plt.json').read_text()).items()}
class Case:
 def __init__(self,name,real_fstab=False):
  self.real_fstab=real_fstab;self.fileline=0;self.name=name;self.u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);self.u.mem_map(0,0x20000);self.u.mem_map(0x100000,0x200000)
  for typ,flags,off,va,_,sz,memsz,al in E.ph:
   if typ==1:self.u.mem_write(va,E.data[off:off+sz])
  self.heap=0x100000;self.events=[];self.pcs=set();self.stubs=set();self.out=bytearray();self.position=0;self.wcalls=0;self.rcalls=0;self.fstab_calls=0
  self.errno=self.alloc(b'\0'*8);self.putptr(0x10c30,self.alloc(b'CANARY!!'));self.u.hook_add(UC_HOOK_CODE,self.code);self.u.hook_add(UC_HOOK_INTR,self.intr)
 def alloc(self,data):
  a=self.heap;self.heap+=(len(data)+15)//16*16;assert self.heap<0x200000;self.u.mem_write(a,data);return a
 def putptr(self,a,v):self.u.mem_write(a,struct.pack('<Q',v))
 def ptr(self,a):return struct.unpack('<Q',self.u.mem_read(a,8))[0]
 def string(self,a):return bytes(self.u.mem_read(a,8192)).split(b'\0')[0]
 def args(self):return [self.u.reg_read(r) for r in REG]
 def ret(self,v=0):self.u.reg_write(REG[0],v&((1<<64)-1));self.u.reg_write(UC_ARM64_REG_PC,self.u.reg_read(UC_ARM64_REG_LR))
 def error(self,n):self.u.mem_write(self.errno,struct.pack('<I',n));self.ret(-1)
 def intr(self,*args):raise AssertionError('OEM syscall forbidden')
 def cxx(self,a,data):
  if len(data)<23:self.u.mem_write(a,bytes([len(data)*2])+data+b'\0'*(23-len(data)))
  else:self.u.mem_write(a,struct.pack('<QQQ',((len(data)+16)//16*16)|1,len(data),self.alloc(data+b'\0')))
 def fstab(self):
  self.fstab_calls+=1;path=self.string(self.args()[0]).decode();assert path=='/fstab.mt8163';self.events.append({'fstab_read_stub':path})
  if self.name=='fstab_fail' or (self.name=='writer_fstab_fail' and self.fstab_calls==2):self.ret(0);return
  records=[]
  for line in FSTAB.splitlines():
   if not line.strip() or line.startswith('#'):continue
   fields=line.split()
   if self.name=='missing_misc' and fields[1]=='/misc':continue
   records.append(struct.pack('<QQQ',*[self.alloc(t.encode()+b'\0') for t in fields[:3]])+bytes(72))
  base=self.alloc(b''.join(records));self.ret(self.alloc(struct.pack('<I4xQQ',len(records),base,0)))
 def code(self,u,pc,size,_):
  if pc==0x2f0000:u.emu_stop();return
  self.pcs.add(pc)
  a,b,c,d,e,f=self.args()
  if pc==0xb004:
   if not self.real_fstab:self.stubs.add('fs_mgr_read_fstab at 0xb004');self.fstab();return
   self.fstab_calls+=1;self.events.append({'real_fstab_parser':self.string(a).decode()})
  if pc==0xbf18:self.stubs.add('fs_mgr log at 0xbf18');self.ret();return
  if pc==0x8f88:self.stubs.add('ALOG at 0x8f88');self.events.append({'log_format':self.string(c).decode()});self.ret();return
  if pc==0x8860:self.stubs.add('StringPrintf at 0x8860');self.cxx(self.u.reg_read(UC_ARM64_REG_X8),b'fixture error');self.ret();return
  if pc==0x6bdc:self.stubs.add('error string concatenate at 0x6bdc');self.cxx(self.u.reg_read(UC_ARM64_REG_X8),b'fixture error');self.ret();return
  if pc==0x6cb0:self.stubs.add('error string assign at 0x6cb0');self.cxx(a,bytes(u.mem_read(b,c)));self.ret(a);return
  if pc==0x574c:self.stubs.add('error string dispose at 0x574c');self.ret();return
  if pc in PLT:
   n=PLT[pc];self.stubs.add(n)
   if n=='strcmp':self.ret(0 if self.string(a)==self.string(b) else 1)
   elif n=='strncmp':self.ret(0 if self.string(a)[:c]==self.string(b)[:c] else 1)
   elif n=='__strlen_chk':self.ret(len(self.string(a)))
   elif n in ('memcpy','memmove'):u.mem_write(a,bytes(u.mem_read(b,c)));self.ret(a)
   elif n=='memset':u.mem_write(a,bytes([b&255])*c);self.ret(a)
   elif n=='_Znwm':self.ret(self.alloc(bytes(a)))
   elif n in ('_ZdlPv','__cxa_atexit'):self.ret()
   elif n=='__system_property_get':
    assert self.string(a)==b'ro.hardware';s=b'' if self.name=='no_hardware' else b'mt8163';u.mem_write(b,s+b'\0');self.ret(len(s))
   elif n=='__snprintf_chk':
    assert self.string(e)==b'ANDROID_SOCKET_%s' and self.string(f)==b'uncrypt';s=b'ANDROID_SOCKET_uncrypt';u.mem_write(a,s+b'\0');self.ret(len(s))
   elif n=='getenv':assert self.string(a)==b'ANDROID_SOCKET_uncrypt';self.ret(self.alloc(b'10\0'))
   elif n=='__errno':self.ret(self.errno)
   elif n in ('strtol','strtoll'):
    raw=self.string(a).decode();self.ret(int(raw,10 if c in (0,10) else c))
   elif n=='fopen':
    assert self.string(a)==b'/fstab.mt8163' and self.string(b)==b'r';self.fileline=0;self.events.append({'fopen_stub':'/fstab.mt8163','mode':'r'});self.ret(51)
   elif n=='getline':
    assert c==51;lines=FSTAB.splitlines(keepends=True)
    if self.fileline==len(lines):self.ret(-1)
    else:
     data=lines[self.fileline].encode();self.fileline+=1;self.putptr(a,self.alloc(data+b'\0'));self.putptr(b,len(data)+1);self.ret(len(data))
   elif n=='fseek':assert (a,b,c)==(51,0,0);self.fileline=0;self.ret()
   elif n=='fclose':assert a==51;self.events.append({'fclose_stub':51});self.ret()
   elif n=='atoi':self.ret(int(self.string(a)))
   elif n=='isspace':self.ret(int(a in (9,10,11,12,13,32)))
   elif n=='calloc':self.ret(self.alloc(bytes(a*b)))
   elif n=='free':self.ret()
   elif n=='strdup':self.ret(self.alloc(self.string(a)+b'\0'))
   elif n=='strndup':self.ret(self.alloc(self.string(a)[:b]+b'\0'))
   elif n=='strtok_r':
    p=a or self.ptr(c);delims=self.string(b)
    while p and self.u.mem_read(p,1)[0] in delims:p+=1
    if not p or self.u.mem_read(p,1)[0]==0:self.putptr(c,p);self.ret(0)
    else:
     start=p
     while self.u.mem_read(p,1)[0] and self.u.mem_read(p,1)[0] not in delims:p+=1
     if self.u.mem_read(p,1)[0]:self.u.mem_write(p,b'\0');p+=1
     self.putptr(c,p);self.ret(start)
   elif n in ('__strchr_chk','__strrchr_chk'):
    raw=self.string(a);pos=(raw.rfind(bytes([b])) if n=='__strrchr_chk' else raw.find(bytes([b]))) if b else len(raw);self.ret(0 if pos<0 else a+pos)
   elif n=='__strlcat_chk':
    old=self.string(a);new=self.string(b);self.u.mem_write(a,(old+new)[:c-1]+b'\0');self.ret(len(old)+len(new))
   elif n=='fcntl':assert (a,b,c)==(10,2,1);self.ret()
   elif n=='listen':assert (a,b)==(10,1);self.events.append({'listen_stub':a});self.ret()
   elif n=='accept4':assert (a,b,c,d)==(10,0,0,0x80000);self.events.append({'accept_stub':11});self.ret(11)
   elif n=='open':
    path=self.string(a).decode()
    if self.real_fstab and path=='/sys/class/BOOT/BOOT/boot/boot_mode':
     assert b==0x88000;self.events.append({'readonly_open_stub':path,'flags':hex(b)});self.ret(13);return
    assert path=='/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/para' and b==0x101001,(path,hex(b),hex(self.u.reg_read(UC_ARM64_REG_LR)))
    self.events.append({'open_stub':path,'flags':hex(b),'initial_offset':0});self.error(13) if self.name=='open_fail' else self.ret(12)
   elif n=='__write_chk':
    data=bytes(u.mem_read(b,c));assert a in (11,12)
    if a==12:
     self.wcalls+=1;assert not any(data) and self.position+c==1088
     if self.name=='write_eintr' and self.wcalls==1:self.events.append({'write_eintr':True});self.error(4);return
     if self.name=='write_fail' or (self.name=='partial_fail' and self.wcalls==2):self.events.append({'write_error_at':self.position});self.error(5);return
     count=min(c,100) if self.name in ('partial_write','partial_fail') else c
     self.events.append({'write_stub':12,'offset':self.position,'length':count,'all_zero':True});self.position+=count;self.ret(count)
    else:
     self.events.append({'status_attempt_hex':data.hex()})
     if self.name=='status_fail':self.error(32);return
     self.out.extend(data);self.ret(c)
   elif n=='fsync':assert a==12;self.events.append({'fsync_stub':a,'fails':self.name=='fsync_fail'});self.error(5) if self.name=='fsync_fail' else self.ret()
   elif n=='__read_chk':
    if self.real_fstab and a==13:
     assert c==3;u.mem_write(b,b'0\n');self.events.append({'readonly_boot_mode_stub':'0'});self.ret(2);return
    assert a==11 and c==4;self.rcalls+=1;self.events.append({'ack_read_stub':c})
    if self.name=='ack_eof':self.ret(0)
    else:u.mem_write(b,b'\xde\xad\xbe\xef' if self.name=='ack_arbitrary' else bytes(4));self.ret(4)
   elif n=='close':assert a in (10,11,12,13);self.events.append({'close_stub':a});self.ret(-1 if self.name=='close_fail' and a==12 else 0)
   elif n=='strerror':self.ret(self.alloc(b'fixture error\0'))
   else:raise AssertionError(('unexpected import',n,hex(pc)))
   return
  ranges=[(0x3b28,0x3d00),(0x3e70,0x4064),(0x40bc,0x4264),(0x42ec,0x4338),(0x4880,0x4890),(0x4ca0,0x4d20),(0x5f2c,0x6098),(0x6438,0x6aa0),(0x6de0,0x6de8),(0x6fcc,0x70d0),(0xba58,0xbb1c),(0xc00c,0xc07c)]
  if self.real_fstab:ranges.extend([(0xb004,0xb980),(0xbb3c,0xbe28)])
  assert any(lo<=pc<hi for lo,hi in ranges),('unexpected instruction',hex(pc))
 def call(self,pc,*args):
  self.u.reg_write(UC_ARM64_REG_SP,0x2e0000);self.u.reg_write(UC_ARM64_REG_LR,0x2f0000)
  for r,v in zip(REG,args):self.u.reg_write(r,v)
  self.u.emu_start(pc,0x2f0004,timeout=1000000,count=150000)
  assert self.u.reg_read(UC_ARM64_REG_PC)==0x2f0000,'instruction/time limit'
  return self.u.reg_read(REG[0])
 def run(self):
  self.call(0x3b28)
  argv=self.alloc(struct.pack('<QQQ',self.alloc(b'/system/bin/uncrypt\0'),self.alloc(b'--clear-bcb\0'),0))
  result=self.call(0x3e70,2,argv)
  fail=self.name in ('open_fail','write_fail','partial_fail','fsync_fail','fstab_fail','writer_fstab_fail','missing_misc','no_hardware')
  assert result==int(fail),(self.name,result)
  if self.name in ('no_hardware','fstab_fail'):assert self.position==0 and not self.out
  elif self.name!='status_fail':assert self.out==bytes.fromhex('ffffffff' if fail else '00000064')
  if self.name in ('success','partial_write','write_eintr','status_fail','ack_eof','ack_arbitrary','close_fail'):assert self.position==1088
  assert 0x4264 not in self.pcs and 0x4064 not in self.pcs
  return dict(name=self.name,real_fstab_parser=self.real_fstab,result=result,bytes_written=self.position,status_hex=self.out.hex(),events=self.events,executed_instructions=len(self.pcs),stubs=sorted(self.stubs),pcs=[hex(x) for x in sorted(self.pcs)])
if __name__=='__main__':
 names=['success','partial_write','write_eintr','open_fail','write_fail','partial_fail','fsync_fail','status_fail','ack_eof','ack_arbitrary','close_fail','fstab_fail','writer_fstab_fail','missing_misc','no_hardware']
 results=[Case(n).run() for n in names]+[Case('success',real_fstab=True).run()]
 assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < 1024**3
 (S/'evidence/oem-emulation.json').write_text(json.dumps(dict(binary_sha256=PIN,passed=len(results),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,cases=results,limits='Single process sequential; 45 CPU sec, 1GiB measured peak RSS ceiling; <=150000 instructions and 1s per entry. All external calls stubbed. No real sockets or unit data.'),indent=2)+'\n')
 print(json.dumps({'passed':len(results)}))
