"""Local unit only: relocate the single clang object and execute its real bytes.
EL/SCTLR reads are supplied by the harness; this is not physical execution.
Uses the already-local camera fixture venv (unicorn/capstone/pyelftools).
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import struct,json,hashlib,re,sys
from elftools.elf.elffile import ELFFile
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ
from unicorn.arm64_const import *
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
R=Path(__file__).resolve().parents[1]; OLD=R.parent/'2026-11-07-asus-linux49-entry-text-checkpoint'
BASE=0x40080000; FDT=0x47000000; RET=0x44400000
elf=ELFFile((R/'qa/unit.o').open('rb')); symtab=elf.get_section_by_name('.symtab')
alloc={};addr=BASE
for i,s in enumerate(elf.iter_sections()):
 if s['sh_flags']&2:
  addr=(addr+4095)&~4095;alloc[i]=(addr,bytearray(s.data()));addr+=len(s.data())
def sym(s):
 idx=s['st_shndx'];return s['st_value']+(alloc[idx][0] if isinstance(idx,int) else 0)
syms={s.name:sym(s) for s in symtab.iter_symbols() if s.name and s['st_shndx']!='SHN_UNDEF'}
for s in elf.iter_sections():
 if s['sh_type']!='SHT_RELA':continue
 target,buf=alloc[s['sh_info']]
 for rel in s.iter_relocations():
  off=rel['r_offset'];p=target+off;a=sym(symtab.get_symbol(rel['r_info_sym']))+rel['r_addend'];typ=rel['r_info_type'];w=struct.unpack_from('<I',buf,off)[0]
  if typ==275:
   imm=((a>>12)-(p>>12))&0x1fffff;w=(w&~((3<<29)|(0x7ffff<<5)))|((imm&3)<<29)|((imm>>2)<<5)
  elif typ==277:w=(w&~(0xfff<<10))|((a&0xfff)<<10)
  else:raise AssertionError(('unexpected relocation',typ))
  struct.pack_into('<I',buf,off,w)
code=bytes(alloc[elf.get_section_index('.text')][1]); cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
ins=list(cs.disasm(code,BASE)); (R/'qa/unit.disasm').write_text('\n'.join(f'{i.address:x}: {i.mnemonic} {i.op_str}' for i in ins)+'\n')
end=syms['asus_entry_text_end'];commit=syms['asus_entry_text_commit']; entry=[i for i in ins if i.address<end]
for i in entry:
 text=i.op_str
 assert not re.search(r'\b(?:sp|[xw](?:[1-3]|1[89]|2[0-9]|30))\b',text),(i.mnemonic,text)
 assert i.mnemonic not in ('bl','blr','ret','stp','ldp')
 assert not re.match(r'[xw]0\b',text) or i.mnemonic in ('cmp','tst')
assert code[commit-BASE:commit-BASE+8]==bytes.fromhex('913800b99f3f03d5')
(R/'qa/unit.text.bin').write_bytes(code)
DT=(OLD/'source/expected-runtime.dtb').read_bytes();tag=json.loads((R/'evidence/identity.json').read_text())['tag'].encode()
def run(blob,expected,pa=FDT,mmu=False,cache=False,bad_oem=False):
 u=Uc(UC_ARCH_ARM64,UC_MODE_ARM)
 for a,b in alloc.values():u.mem_map(a,(len(b)+4095)&~4095);u.mem_write(a,bytes(b))
 u.mem_map(pa&~4095,((len(blob)+(pa&4095)+4095)&~4095));u.mem_write(pa,blob)
 u.mem_map(RET,0x80000);orig=bytearray(b'P'*0x80000)
 struct.pack_into('<7I',orig,0,0 if bad_oem else 0x43474244,64,192,128,320,576,256)
 struct.pack_into('<6I',orig,0x28,*([0xffffffff]*6));u.mem_write(RET,bytes(orig))
 regs=[UC_ARM64_REG_X0+i for i in range(29)]+[UC_ARM64_REG_X29,UC_ARM64_REG_X30]
 for n,r in enumerate(regs):u.reg_write(r,pa if n==0 else 0x123400000000+n)
 u.reg_write(UC_ARM64_REG_SP,0x76543000)
 writes=[];mrs={i.address:i for i in entry if i.mnemonic=='mrs'}
 def hook(uc,a,size,_):
  if a in mrs:
   uc.reg_write(UC_ARM64_REG_X4,4 if 'currentel' in mrs[a].op_str.lower() else int(mmu)|(int(cache)<<2));uc.reg_write(UC_ARM64_REG_PC,a+4)
 def write(uc,access,a,size,value,_):
  assert RET<=a and a+size<=RET+0x80000,('unexpected store',hex(a));writes.append((a,size,value))
 def read(uc,access,a,size,value,_):
  if (pa&~4095)<=a<((pa+len(blob)+4095)&~4095):assert pa<=a and a+size<=pa+len(blob),('FDT out of bounds',hex(a),size,len(blob))
 u.hook_add(UC_HOOK_CODE,hook);u.hook_add(UC_HOOK_MEM_WRITE,write);u.hook_add(UC_HOOK_MEM_READ,read)
 u.emu_start(BASE,end,count=2000000)
 assert u.reg_read(UC_ARM64_REG_PC)==end,'bounded instruction budget exhausted'
 for n in [0,1,2,3,*range(18,31)]:assert u.reg_read(regs[n])==(pa if n==0 else 0x123400000000+n),('ABI',n)
 assert u.reg_read(UC_ARM64_REG_SP)==0x76543000
 actual=bool(writes);assert actual==expected,('admission',actual,expected)
 if expected:
  after=bytes(u.mem_read(RET,0x80000));co=1856
  assert after[:0x28]==orig[:0x28] and after[64:co]==orig[64:co] and after[co+len(tag):]==orig[co+len(tag):]
  assert after[co:co+len(tag)]==tag
  assert struct.unpack_from('<6I',after,0x28)==(0x80000,832,1856,0,len(tag),0x80000-1856)
  assert writes[-1]==(RET+0x38,4,len(tag))
 return dict(admitted=actual,stores=len(writes),ABI_preserved=True)
# Re-encode the existing token tree with mutable ordered property/node lists.
sys.path.insert(0,str(OLD/'source'));import fdt
h,_,tokens=fdt.parse(DT)
def tree():
 stack=[];root=None
 for t,p,n,v,raw in tokens:
  if t==1:
   node=[p.rsplit('/',1)[-1],[],[]]
   if stack:stack[-1][2].append(node)
   else:root=node
   stack.append(node)
  elif t==3:stack[-1][1].append((n,v))
  elif t==2:stack.pop()
 return root
def child(t,name):return next(n for n in t[2] if n[0]==name)
def prop(t,name,value):t[1]=[(n,value if n==name else v) for n,v in t[1]]
def build(t,mr=b'\0'*16):
 strings=bytearray();stream=bytearray()
 def emit(n):
  stream.extend(struct.pack('>I',1)+n[0].encode()+b'\0');stream.extend(bytes(-len(stream)%4))
  for key,v in n[1]:
   off=len(strings);strings.extend(key.encode()+b'\0');stream.extend(struct.pack('>III',3,len(v),off)+v);stream.extend(bytes(-len(stream)%4))
  for c in n[2]:emit(c)
  stream.extend(struct.pack('>I',2))
 emit(t);stream.extend(struct.pack('>I',9));s=40+len(mr)
 return struct.pack('>10I',0xd00dfeed,s+len(stream)+len(strings),s,s+len(stream),40,17,16,0,len(strings),len(stream))+mr+stream+strings
results={}
def case(n,b,ok,**kw):
 try:results[n]=run(b,ok,**kw)
 except Exception as e:
  (R/'qa'/('failure-'+re.sub('[^a-z0-9]+','-',n.lower())+'.dtb')).write_bytes(b)
  (R/'qa/failure.json').write_text(json.dumps(dict(case=n,error=str(e)),indent=2)+'\n');raise
case('packaged input',DT,True)
t=tree();c=child(t,'chosen');prop(c,'bootargs',b'console=tty0 console=ttyMT3,921600n1 ordinary LK handoff\0');prop(c,'linux,initrd-start',struct.pack('>Q',0x44000000));prop(c,'linux,initrd-end',struct.pack('>Q',0x4403f007));case('chosen bootargs and initrd values ignored',build(t),True)
t=tree();t[2].reverse();t[1].reverse();r=child(t,'reserved-memory');r[1].reverse();r[2].reverse()
for c in r[2]:c[1].reverse()
case('reordered critical nodes properties and string offsets',build(t),True)
for value in (b'ok\0',b'okay\0'):
 t=tree();child(child(t,'reserved-memory'),'ram_console-reserved-memory')[1].append(('status',value));case('retained status '+value.decode().strip('\0'),build(t),True)
for name,mut in [
 ('wrong reservation size',lambda t:prop(child(child(t,'reserved-memory'),'ram_console-reserved-memory'),'reg',struct.pack('>QQ',RET,0x40000))),
 ('missing reservation',lambda t:child(t,'reserved-memory')[2].__setitem__(slice(None),[c for c in child(t,'reserved-memory')[2] if c[0]!='ram_console-reserved-memory'])),
 ('competing fixed reservation',lambda t:child(t,'reserved-memory')[2].append(['other',[('reg',struct.pack('>QQ',RET-16,32))],[]])),
 ('duplicate retained node',lambda t:child(t,'reserved-memory')[2].append(child(child(t,'reserved-memory'),'ram_console-reserved-memory'))),
 ('duplicate critical property',lambda t:child(child(t,'reserved-memory'),'ram_console-reserved-memory')[1].append(('reg',struct.pack('>QQ',RET,0x80000)))),
 ('no map',lambda t:child(child(t,'reserved-memory'),'ram_console-reserved-memory')[1].append(('no-map',b''))),
 ('reusable',lambda t:child(child(t,'reserved-memory'),'ram_console-reserved-memory')[1].append(('reusable',b''))),
 ('disabled retained',lambda t:child(child(t,'reserved-memory'),'ram_console-reserved-memory')[1].append(('status',b'disabled\0'))),
 ('wrong compatible',lambda t:prop(child(child(t,'reserved-memory'),'ram_console-reserved-memory'),'compatible',b'other\0')),
 ('root compatible malformed list',lambda t:prop(t,'compatible',b'asus,p00a\0unterminated')),
 ('fake reservation at wrong path',lambda t:child(t,'reserved-memory').__setitem__(0,'unrelated')),
 ('unterminated memory type alias',lambda t:child(t,'chosen')[2].append(['alias',[('device_type',b'memory'),('reg',struct.pack('>QQ',0x40000000,0x10000000))],[]])),
 ('nested memory alias',lambda t:child(t,'chosen')[2].append(['alias',[('device_type',b'memory\0'),('reg',struct.pack('>QQ',0x40000000,0x10000000))],[]])),
 ('memory type trailing bytes',lambda t:prop(child(t,'memory@00000000'),'device_type',b'memory\0hidden')),
 ('usable memory override',lambda t:child(t,'memory@00000000')[1].append(('linux,usable-memory',struct.pack('>QQ',0x40000000,0x10000000)))),
 ('wrong memory bank',lambda t:prop(child(t,'memory@00000000'),'reg',struct.pack('>QQ',0x40000000,0x7d500000))),
]:
 t=tree();mut(t);case(name,build(t),False)
t=tree();prop(t,'compatible',b'other,board\0asus,p00a\0');case('root compatible bounded list membership',build(t),True)
case('memreserve overlap',build(tree(),struct.pack('>QQ',RET,0x80000)+bytes(16)),False)
for name,offset,value in [('u32 totalsize',4,0xffffffff),('u32 structure size',36,0xffffffff),('overlapping blocks',12,h[2]),('bad string offset',h[2]+8+8,0xffffffff),('unaligned structure',8,h[2]+1),('unbounded memreserve',16,len(DT)&~7)]:
 b=bytearray(DT);struct.pack_into('>I',b,offset,value);case(name,bytes(b),False)
case('MMU enabled',DT,False,mmu=True);case('D cache enabled',DT,False,cache=True);case('OEM signature invalid',DT,False,bad_oem=True)
result=dict(status='LOCAL_SINGLE_OBJECT_ASSEMBLY_AND_FOCUSED_EXECUTION_PASSED',object_sha256=hashlib.sha256((R/'qa/unit.o').read_bytes()).hexdigest(),entry_bytes=end-BASE,entry_sha256=hashlib.sha256(code[:end-BASE]).hexdigest(),cases=results,EL_SCTLR='modeled register reads only',physical_execution=False,kernel_build=False)
(R/'evidence/local-check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
