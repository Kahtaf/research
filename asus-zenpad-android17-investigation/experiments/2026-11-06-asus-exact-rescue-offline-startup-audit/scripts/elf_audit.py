"""Small bounded ELF64 reader and AArch64 ADR/ADRP+ADD string cross-reference finder.

Raw instruction references are candidates for manual disassembly review, not a CFG proof.
"""
import pathlib,struct,re,json,hashlib,resource
resource.setrlimit(resource.RLIMIT_CPU,(45,45))
R=pathlib.Path(__file__).resolve().parents[1]
def elf(path):
 b=path.read_bytes();assert b[:6]==b'\x7fELF\x02\x01'
 fields=struct.unpack_from('<HHIQQQIHHHHHH',b,16)
 typ,machine,ver,entry,phoff,shoff,flags,ehsz,phsz,phn,shsz,shn,shstr=fields
 ph=[struct.unpack_from('<IIQQQQQQ',b,phoff+i*phsz) for i in range(phn)]
 sh=[struct.unpack_from('<IIQQQQIIQQ',b,shoff+i*shsz) for i in range(shn)]
 strsec=sh[shstr];names=b[strsec[4]:strsec[4]+strsec[5]]
 sections=[]
 for s in sh:
  name=names[s[0]:].split(b'\0')[0].decode()
  sections.append(dict(name=name,address=hex(s[3]),offset=s[4],bytes=s[5],flags=s[2]))
 strings=[];stringmap={}
 for p in ph:
  t,f,off,va,pa,sz,memsz,al=p
  if t!=1:continue
  for m in re.finditer(rb'[ -~]{4,}\x00',b[off:off+sz]):
   s=m.group()[:-1].decode();addr=va+m.start();stringmap[addr]=s
   if any(x in s.lower() for x in ('restorecon','selinux','init.rc','ueventd','usb','/init','/sbin/','/proc/self','adbd','second-stage','root_seclabel','error','fail','coldboot','ep0','property','secure','socket')):
    strings.append(dict(address=hex(addr),offset=off+m.start(),text=s))
 selected={int(s['address'],16):s['text'] for s in strings};refs=[]
 sx=lambda n,bits:n-(1<<bits) if n&(1<<(bits-1)) else n
 for p in ph:
  t,f,off,va,pa,sz,memsz,al=p
  if t!=1 or not f&1:continue
  regs={}
  for i in range(0,sz-3,4):
   pc=va+i;ins=struct.unpack_from('<I',b,off+i)[0];rd=ins&31
   # ADRP and ADR are PC relative, immediate is signed 21 bits.
   if ins&0x9f000000 in (0x90000000,0x10000000):
    imm=sx(((ins>>5)&0x7ffff)<<2|((ins>>29)&3),21)
    value=(pc&~4095)+(imm<<12) if ins&0x80000000 else pc+imm
    regs[rd]=(value,pc)
    if value in selected:refs.append(dict(instruction=hex(pc),target=hex(value),text=selected[value]))
   elif ins&0x7f000000==0x11000000:
    rn=(ins>>5)&31;imm=(ins>>10)&4095;imm<<=12 if ins&(1<<22) else 0
    if rn in regs and pc-regs[rn][1]<=48:
     value=regs[rn][0]+imm;regs[rd]=(value,pc)
     if value in selected:refs.append(dict(instruction=hex(pc),target=hex(value),text=selected[value]))
    else:regs.pop(rd,None)
   # Conservative expiry; disassembly must confirm dataflow for every conclusion.
   regs={n:v for n,v in regs.items() if pc-v[1]<=48}
 return dict(path=str(path),sha256=hashlib.sha256(b).hexdigest(),elf_type=typ,machine=machine,entry=hex(entry),program_headers=[dict(type=p[0],flags=p[1],offset=p[2],address=hex(p[3]),file_bytes=p[5],memory_bytes=p[6]) for p in ph],static=not any(p[0] in (2,3) for p in ph),sections=sections,strings=strings,string_references=refs)
report={}
for n in ('init','sbin/adbd','sbin/rescue-proxy','sbin/os-rescue'):
 path=R/'extracted/candidate'/n;r=elf(path)
 stock=R/'extracted/stock'/n
 if stock.exists():r['identical_to_stock']=path.read_bytes()==stock.read_bytes()
 report[n]=r
(R/'evidence/elf-audit.json').write_text(json.dumps(report,indent=2)+'\n')
for n,r in report.items():
 print(n,r['sha256'],'static',r['static'],'stock_equal',r.get('identical_to_stock'))
 for ref in r['string_references']:
  if any(s in ref['text'] for s in ('/proc/self/attr/current','restorecon','cannot execv','/dev/usb-ffs/adb/ep0','sys.usb.ffs.ready','cannot setexeccon','/system/bin/sh','/sbin/adbd','--second-stage','Unable to load SELinux')):print(ref)
