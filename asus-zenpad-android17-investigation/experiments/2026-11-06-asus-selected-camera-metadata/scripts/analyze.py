from pathlib import Path
from elftools.elf.elffile import ELFFile
from capstone import *
import re,json,struct
ROOT=Path(__file__).resolve().parents[1]
class Binary:
 def __init__(self,p):
  self.p=Path(p);self.f=self.p.open('rb');self.e=ELFFile(self.f);self.bits=self.e.elfclass;self.ps=self.bits//8
  self.syms=list(self.e.get_section_by_name('.dynsym').iter_symbols());self.names={s.name:s for s in self.syms};self.addrs={s['st_value']&~1:s.name for s in self.syms if s['st_value']}
  self.rel={}
  for sec in self.e.iter_sections():
   if sec['sh_type'] in ['SHT_REL','SHT_RELA']:
    for r in sec.iter_relocations():self.rel[r['r_offset']]=(self.syms[r['r_info_sym']].name,r.entry.get('r_addend',None))
 def read(self,a,n):
  for s in self.e.iter_segments():
   if s['p_type']=='PT_LOAD' and s['p_vaddr']<=a and a+n<=s['p_vaddr']+s['p_filesz']:
    self.f.seek(s['p_offset']+a-s['p_vaddr']);return self.f.read(n)
  return bytes(n)
 def ptr(self,a):return int.from_bytes(self.read(a,self.ps),'little')
 def string(self,a):return self.read(a,200).split(b'\0')[0].decode(errors='replace')
 def dis(self,s):
  a=s['st_value']&~1;cs=Cs(CS_ARCH_ARM if self.bits==32 else CS_ARCH_ARM64,(CS_MODE_THUMB if s['st_value']&1 else CS_MODE_ARM) if self.bits==32 else CS_MODE_ARM);cs.detail=True
  out=[f"\n{s.name if hasattr(s, 'name') else s['name']} @{a:#x} size={s['st_size']:#x} mode={'thumb' if s['st_value']&1 else 'arm/a64'}"]
  for i in cs.disasm(self.read(a,s['st_size']),a):
   note=''
   if self.bits==32 and i.mnemonic.startswith('ldr') and '[pc,' in i.op_str:
    m=re.search(r'\[pc, #(-?0x[0-9a-f]+|-?[0-9]+)\]',i.op_str)
    if m:
     loc=((i.address+(4 if s['st_value']&1 else 8))&~3)+int(m[1],0);val=int.from_bytes(self.read(loc,4),'little');note=f' literal[{loc:#x}]={val:#x}'
   if i.mnemonic in ['bl','blx','b'] and i.op_str.startswith('#'):
    addr=int(i.op_str[1:],0);note+=' '+self.addrs.get(addr,'')
   out.append(f'{i.address:08x}: {i.bytes.hex():12} {i.mnemonic:8} {i.op_str}{note}')
  return '\n'.join(out)
if __name__=='__main__':
 inventory={}
 for p in sorted((ROOT/'inputs').glob('*.so')):
  b=Binary(p);inv={'exports':[{'name':s.name,'address':hex(s['st_value']),'size':s['st_size']} for s in b.syms if s['st_shndx']!='SHN_UNDEF'],'imports':[s.name for s in b.syms if s['st_shndx']=='SHN_UNDEF']};inventory[p.name]=inv
  selected=[s for s in b.syms if s['st_info']['type']=='STT_FUNC' and s['st_size'] and re.search('MetadataProvider|TemplateRequest|DngInfo|HalSensorList|SensorInfo|GetSensorInitFuncList',s.name) and not re.search('SortedVector|Manager',s.name)]
  (ROOT/'evidence'/(p.name+'.dis.txt')).write_text('\n'.join(b.dis(s) for s in selected))
  (ROOT/'evidence'/(p.name+'.strings.json')).write_text(json.dumps([{'address':hex(m.start()),'text':m.group().decode()} for m in re.finditer(rb'[ -~]{5,}',p.read_bytes())],indent=2))
 (ROOT/'evidence/inventory.json').write_text(json.dumps(inventory,indent=2))
