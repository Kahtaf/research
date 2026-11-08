"""Offline exact Thumb execution; synthetic RAM, USB and storage only.
No device libraries, subprocess, network or host block-device opens.
One sequential Unicorn CPU, <64 MiB mapped RAM, per-call 100k instructions/2 s.
"""
from pathlib import Path
import hashlib,json,struct,resource
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.arm_const import *
S=Path(__file__).resolve().parents[1];W=S.parent
LK=W/'2026-11-05-asus-boot-access-audit/sources/firmware/lk.bin'
B=LK.read_bytes();BASE=0x41e00000;GOT=0x41e6500c
assert hashlib.sha256(B).hexdigest()=='c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765'
N=16740352;START=160184*512;BUF=0x45000000;ARG=0x43020000;END=0x430ff000
RP=W/'2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin'
REC=RP.read_bytes();assert len(REC)==N and hashlib.sha256(REC).hexdigest()=='902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
# No private data: only this publicly distributable original recovery image.
REGS=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]
PINS={};RESULTS=[]
class F:
 def __init__(self):
  self.u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);self.u.mem_map(BASE,0x100000);self.u.mem_write(BASE,B[512:])
  self.u.mem_map(0x43000000,0x100000);self.u.mem_map(BUF,0x2000000)
  self.hooks={};self.allowed=[];self.events=[];self.trace=[];self.heap=0x43040000;self.stops={END};self.stubbed=set()
  self.u.hook_add(UC_HOOK_CODE,self.code);self.u.hook_add(UC_HOOK_INTR,lambda *a:(_ for _ in ()).throw(AssertionError('interrupt forbidden')))
  self.hooks.update({0x41e25bf4:self.strcmp,0x41e25b8c:self.memcmp,0x41e25cbc:self.strncmp,0x41e25c88:lambda:self.ret(len(self.string(self.a()[0]))),0x41e25c10:self.strcpy,0x41e259bc:self.memcpy,0x41e25ac8:self.memset,0x41e2591c:self.snprintf,0x41e25948:self.sprintf,0x41e25968:self.malloc})
  for p in [0x41e24dac,0x41e24b40,0x41e25370]:self.hooks[p]=lambda:self.ret(0)
  self.hooks[0x41e1e648]=self.send
 def a(self):return [self.u.reg_read(r) for r in REGS]
 def word(self,a):return struct.unpack('<I',self.u.mem_read(a,4))[0]
 def put(self,a,v):self.u.mem_write(a,struct.pack('<I',v&0xffffffff))
 def string(self,a):return bytes(self.u.mem_read(a,2048)).split(b'\0')[0].decode('ascii') if a else ''
 def ret(self,v=0,hi=None):
  self.u.reg_write(UC_ARM_REG_R0,v&0xffffffff)
  if hi is not None:self.u.reg_write(UC_ARM_REG_R1,hi&0xffffffff)
  self.u.reg_write(UC_ARM_REG_PC,self.u.reg_read(UC_ARM_REG_LR))
 def code(self,u,pc,size,_):
  if pc in self.stops:u.emu_stop();return
  if pc in self.hooks:self.stubbed.add(hex(pc));self.hooks[pc]();return
  assert any(a<=pc<b for a,b in self.allowed),f'unapproved original PC {pc:x}'
  assert BASE<=pc<BASE+len(B)-512
  PINS[f'{pc:08x}']=bytes(u.mem_read(pc,size)).hex();self.trace.append(hex(pc))
 def call(self,pc,*args):
  self.u.reg_write(UC_ARM_REG_SP,0x430f0000);self.u.reg_write(UC_ARM_REG_LR,END|1)
  for r,v in zip(REGS,args):self.u.reg_write(r,v)
  self.u.emu_start(pc|1,END+4,timeout=2000000,count=100000)
  assert self.u.reg_read(UC_ARM_REG_PC) in self.stops,'execution budget exceeded'
  return self.u.reg_read(UC_ARM_REG_R0)
 def strcmp(self):a,b,_,_=self.a();x,y=self.string(a),self.string(b);self.ret((x>y)-(x<y))
 def strncmp(self):a,b,n,_=self.a();x,y=self.string(a)[:n],self.string(b)[:n];self.ret((x>y)-(x<y))
 def memcmp(self):a,b,n,_=self.a();assert n<2048;x,y=bytes(self.u.mem_read(a,n)),bytes(self.u.mem_read(b,n));self.ret((x>y)-(x<y))
 def strcpy(self):a,b,_,_=self.a();self.u.mem_write(a,self.string(b).encode()+b'\0');self.ret(a)
 def memcpy(self):a,b,n,_=self.a();assert n<=N;self.u.mem_write(a,bytes(self.u.mem_read(b,n)));self.ret(a)
 def memset(self):a,v,n,_=self.a();assert n<4097;self.u.mem_write(a,bytes([v&255])*n);self.ret(a)
 def fmt(self,d,cap,fmt,vals):
  import re
  def sub(m):
   v=vals.pop(0);typ=m.group()[-1]
   if typ=='s':return self.string(v)
   return m.group()%v
  text=re.sub(r'%0?\d*[sdx]',sub,fmt);out=text.encode()[:cap-1];self.u.mem_write(d,out+b'\0');self.ret(len(text))
 def snprintf(self):d,n,p,v=self.a();sp=self.u.reg_read(UC_ARM_REG_SP);self.fmt(d,n,self.string(p),[v]+[self.word(sp+i*4) for i in range(6)])
 def sprintf(self):d,p,a,b=self.a();self.fmt(d,1024,self.string(p),[a,b])
 def malloc(self):n=self.a()[0];a=self.heap;self.heap+=(n+15)&~15;assert self.heap<0x430e0000;self.ret(a)
 def send(self):a,n,_,_=self.a();self.events.append({'protocol':bytes(self.u.mem_read(a,n)).decode('ascii')});self.ret(n)
 def save(self,name,**extra):
  r=dict(name=name,events=self.events,stub_addresses=sorted(self.stubbed),instructions=len(self.trace),executed_addresses=sorted(set(self.trace)),**extra);RESULTS.append(r);return r
 def responses(self):return [e['protocol'] for e in self.events if 'protocol'in e]
 def protocol(self):self.allowed +=[(0x41e1e6b8,0x41e1e708),(0x41e1e750,0x41e1e75a),(0x41e1e91c,0x41e1e92c)];self.put(0x41e711c4,1)

def registration():
 f=F();f.allowed=[(0x41e1ea08,0x41e1ee30),(0x41e1e500,0x41e1e55c)]
 for a in [0x41e1ca04,0x41e1cae8,0x41e001dc,0x41e1e92c]:f.hooks[a]=lambda:f.ret()
 f.hooks[0x41e3aae4]=lambda:f.ret(1);f.hooks[0x41e3ab10]=lambda:f.ret(0)
 def warranty():f.put(f.a()[0],0);f.ret()
 f.hooks[0x41e3a24c]=warranty;f.hooks[0x41e1a7e8]=lambda:f.ret(0)
 f.stops.add(0x41e1ed56);f.call(0x41e1ea08,BUF)
 # Registration list global is resolved from original instructions, no fabricated records.
 got_slot=(f.word(0x41e1e538)+0x41e1e52a)&0xffffffff
 head=f.word(f.word(got_slot));rows=[]
 while head:
  rows.append(dict(name=f.string(f.word(head+4)),length=f.word(head+8),secure_flag=f.word(head+12),unlock_required=f.word(head+16),handler=hex(f.word(head+20)&~1),node=hex(head)))
  head=f.word(head)
 assert len(rows)==30,len(rows)
 for n in ['flash:','download:','getvar:']:
  r=next(x for x in rows if x['name']==n);assert (r['secure_flag'],r['unlock_required'])==(1,0)
 assert next(x for x in rows if x['name']=='boot')['unlock_required']==1
 f.save('registration',commands=rows)
 return rows

def dispatch(row,secure=1,unlocked=0):
 f=F();f.allowed=[(0x41e1e83e,0x41e1e8ce)];f.protocol();node=0x43010000
 f.put(node+8,row['length']);f.put(node+12,row['secure_flag']);f.put(node+16,row['unlock_required']);f.put(node+20,int(row['handler'],16)|1)
 f.u.reg_write(UC_ARM_REG_R7,node);f.u.reg_write(UC_ARM_REG_R9,0x41e701ac) # logging only
 f.u.reg_write(UC_ARM_REG_R4,row['length']);f.u.reg_write(UC_ARM_REG_R5,0x41e711c4)
 f.u.reg_write(UC_ARM_REG_R8,0x41e78434);f.u.reg_write(UC_ARM_REG_R11,0x41e7842c)
 f.put(0x41e78434,BUF);f.put(0x41e7842c,N)
 f.hooks[0x41e3b218]=lambda:f.ret(secure);f.hooks[0x41e392dc]=lambda:f.ret(1);f.hooks[0x41e3ab10]=lambda:f.ret(unlocked)
 def handler():f.events.append({'handler_reached':row['handler'],'args':f.a()[:3]});f.put(0x41e711c4,2);f.ret()
 f.hooks[int(row['handler'],16)]=handler;f.stops.add(0x41e1e7bc)
 f.call(0x41e1e83e)
 called=any('handler_reached'in e for e in f.events);assert called==(not row['unlock_required'] or bool(unlocked))
 f.save('dispatcher_'+row['name']+f'_secure{secure}_unlocked{unlocked}')

def handshake(name):
 f=F();f.allowed=[(0x41e1f288,0x41e1f31e)];f.protocol();f.u.mem_write(ARG,name.encode()+b'\0');f.call(0x41e1f288,ARG,BUF,N)
 flag=f.word(0x41e73358);assert flag==(1 if name=='sofia_support' else 0)
 f.save('getvar_'+name,flash_session_flag=flag)
 return flag

def flash(flag=0,policy=True,policy_lock=0,magic=True,length=N,part=True,write_fail=False,erase_fail=False,custom=False):
 f=F();f.allowed=[(0x41e23338,0x41e23754),(0x41e3ab9c,0x41e3ac30),(0x41e21f24,0x41e22046),(0x41e21844,0x41e219f6),(0x41e2147c,0x41e21496)]
 f.protocol();f.u.mem_write(ARG,b'recovery\0');f.u.mem_write(BUF,REC)
 if custom:f.u.mem_write(BUF+4096,b'custom!!')
 if not magic:f.u.mem_write(BUF,b'INVALID!')
 f.put(0x41e73358,flag)
 if policy:
  f.put(0x41e74734,0x43030000);f.put(0x4303000c,policy_lock)
 f.hooks[0x41e3a1c8]=lambda:f.ret()
 for a in [0x41e059ec,0x41e05a74]:f.hooks[a]=lambda:f.ret(123)
 def lookup():assert f.string(f.a()[0])=='recovery';f.events.append({'partition_lookup':'recovery'});f.ret(9 if part else -1)
 f.hooks[0x41e13fe4]=lookup;f.hooks[0x41e14074]=lambda:f.ret(START,0);f.hooks[0x41e14044]=lambda:f.ret(8);f.hooks[0x41e140b4]=lambda:f.ret(N,0)
 def io(kind):
  a=f.a();sp=f.u.reg_read(UC_ARM_REG_SP);addr=a[2]+(a[3]<<32)
  size=f.word(sp)+(f.word(sp+4)<<32) if kind=='erase' else f.word(sp+8)+(f.word(sp+12)<<32)
  e=dict(operation=kind,hardware_part=a[0],offset=addr,length=size)
  if kind=='write':
   e['buffer']=hex(f.word(sp));e['payload_sha256']=hashlib.sha256(bytes(f.u.mem_read(f.word(sp),size))).hexdigest()
  f.events.append(e);assert addr==START and size<=N and a[0]==8
  if kind=='erase':f.ret(-1 if erase_fail else 0)
  else:f.ret(size-512 if write_fail else size,0)
 f.hooks[0x41e141b8]=lambda:io('erase');f.hooks[0x41e1416c]=lambda:io('write')
 f.call(0x41e23338,ARG,BUF,length)
 ops=[e for e in f.events if 'operation'in e]
 expected=bool(flag and magic and 0<length<=N and part)
 assert bool(ops)==expected
 if expected:assert [e['operation'] for e in ops]==['erase','write'] and ops[0]['length']==N and ops[1]['length']==length
 if flag==0 and length:assert not any('partition_lookup'in e for e in f.events)
 f.save(f'flash_flag{flag}_policy{policy}_{policy_lock}_magic{magic}_len{length}_part{part}_writefail{write_fail}_erasefail{erase_fail}_custom{custom}')

def download(mode='complete',length=N):
 f=F();f.allowed=[(0x41e22a24,0x41e22eb8),(0x41e2149c,0x41e21598)];f.protocol()
 f.put(0x41e78434,BUF);f.put(0x41e78440,BUF);f.u.mem_write(ARG,f'{length:08x}'.encode()+b'\0')
 def recv():
  ptr,n,*_=f.a();f.events.append({'usb_receive_request':n,'destination':hex(ptr)})
  data=REC[:n] if mode=='complete' else REC[:28]
  f.u.mem_write(ptr,data);f.ret(n if mode=='complete' else (28 if mode=='short' else -1))
 f.hooks[0x41e1e588]=recv
 f.call(0x41e22a24,ARG,BUF,0)
 f.save('download_'+mode,advertised_length=length,published_length=f.word(0x41e7842c),fastboot_state=f.word(0x41e711c4),buffer_sha256=hashlib.sha256(bytes(f.u.mem_read(BUF,N))).hexdigest())
 assert not any('operation'in e for e in f.events)
 if mode=='complete':assert f.responses()==[f'DATA{length:08x}','OKAY'] and f.word(0x41e7842c)==length
 else:assert f.word(0x41e711c4)==3 and 'OKAY' not in f.responses()

def storage(kind,trim_support=True):
 f=F();f.allowed=[(0x41e1416c,0x41e14190),(0x41e141b8,0x41e141e2),(0x41e1b32c,0x41e1b34a),(0x41e1aca8,0x41e1afac),(0x41e1911c,0x41e191a2),(0x41e191cc,0x41e192ca),(0x41e17ea0,0x41e17fbe)]
 dev,blk,card,host=0x43060000,0x43061000,0x43062000,0x43063000
 f.put(0x41e6b5ac,dev)
 for a,v in [(dev,1),(dev+4,0),(dev+8,blk),(dev+0x14,0x41e1aca9),(dev+0x18,0x41e191f5),(blk+0x14,512),(blk+0x68,0x41e191cd),(blk+0x64,0x41e191a5),(card,host),(card+4,30535680),(card+8,512),(card+0x1c,1)]:f.put(a,v)
 f.u.mem_write(blk+0x18,b'\x09');f.u.mem_write(card+0x20,b'\x10\x00');f.u.mem_write(card+0x26a,b'\x20\x00');f.u.mem_write(card+0x133,b'\x10' if trim_support else b'\x00');f.u.mem_write(card+0x10c,b'\x07')
 f.hooks[0x41e17838]=lambda:f.ret(host);f.hooks[0x41e17848]=lambda:f.ret(card)
 def div():
  a,b,c,d=f.a();q,r=divmod(a+(b<<32),c+(d<<32));f.u.reg_write(UC_ARM_REG_R2,r&0xffffffff);f.u.reg_write(UC_ARM_REG_R3,r>>32);f.ret(q&0xffffffff,q>>32)
 f.hooks[0x41e38584]=div
 def command():
  h,p,*_=f.a();assert h==host;f.events.append({'mmc_command':f.word(p),'argument':f.word(p+4)});f.ret(0)
 f.hooks[0x41e1785c]=command
 def status():f.put(f.a()[2],0x800);f.ret(0)
 f.hooks[0x41e17d20]=status;f.hooks[0x41e17804]=lambda:f.ret(0)
 def write():
  controller,sector,count,p=f.a();f.events.append({'mmc_write':True,'controller':controller,'start_sector':sector,'sector_count':count,'buffer':hex(p)})
  assert (controller,sector,count,p)==(0,160184,32696,BUF);f.ret(0)
 f.hooks[0x41e18360]=write
 sp=0x430f0000
 if kind=='erase':f.put(sp,N);f.put(sp+4,0);result=f.call(0x41e141b8,8,0,START,0)
 else:f.put(sp,BUF);f.put(sp+8,N);f.put(sp+12,0);result=f.call(0x41e1416c,8,0,START,0)
 if kind=='erase':
  assert f.events[:2]==[{'mmc_command':35,'argument':160184},{'mmc_command':36,'argument':192879}]
  if trim_support:assert f.events[2:]==[{'mmc_command':38,'argument':1}] and result==0
  else:assert len(f.events)==2 and result==5
 else:assert result==N
 f.save('storage_'+kind+f'_trim_support{trim_support}',result=result,geometry_and_card_flags_synthetic=True)

def lookup():
 f=F();f.allowed=[(0x41e13fe4,0x41e14038)];f.u.mem_write(ARG,b'recovery\0');index=f.call(0x41e13fe4,ARG);assert index==9;f.save('public_partition_alias_recovery',index=index)

lookup()
storage('erase');storage('erase',False);storage('write')
rows=registration()
for n in ['flash:','download:','boot']:
 for sec in [0,1]:dispatch(next(x for x in rows if x['name']==n),sec)
dispatch(next(x for x in rows if x['name']=='boot'),1,1)
handshake('product');handshake('sofia_support')
for pol in [False,True]:
 for lock in [0,1]:flash(policy=pol,policy_lock=lock)
flash(flag=1);flash(flag=1,policy=False);flash(flag=1,custom=True);flash(flag=1,magic=False);flash(flag=1,length=N+1);flash(flag=1,length=N-512);flash(flag=1,part=False);flash(flag=1,write_fail=True);flash(flag=1,erase_fail=True);flash(flag=1,length=0)
for mode in ['complete','short','error']:download(mode)
(S/'evidence/emulation.json').write_text(json.dumps(dict(cases=RESULTS,case_count=len(RESULTS),limits={'per_call_instructions':100000,'per_call_timeout_us':2000000,'mapped_bytes':0x2200000,'cpu_instances_concurrent':1},all_IO_synthetic=True),indent=2)+'\n')
(S/'evidence/instruction-pins.json').write_text(json.dumps(PINS,indent=2)+'\n')
print(f'{len(RESULTS)} cases passed; {len(PINS)} original instructions pinned; peak RSS {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}')
