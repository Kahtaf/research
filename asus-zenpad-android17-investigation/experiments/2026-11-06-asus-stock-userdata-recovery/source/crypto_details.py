from pathlib import Path
import json,struct
from elfaudit import ELF
from elftools.elf.elffile import ELFFile
S=Path(__file__).resolve().parents[1]
for f,ranges in [('system__bin_vold',[('footer-read',0x738c0,0x73c04),('wipe-on-crypt-fail',0x75d90,0x75ed0),('key-location',0x77ff0,0x782f0)]),('boot__init',[('crypto-dispatch',0x406cc0,0x406f20),('fs-mgr-data',0x42f980,0x430040)]),('recovery__sbin_recovery',[('formatter-start',0x414750,0x414c00),('emmc-bcb-write',0x40e1a0,0x40e2e8),('device-methods',0x401914,0x401a08)])]:
 e=ELF(S/'inputs'/f)
 for name,a,b in ranges:(S/f'evidence/{f}-{name}.txt').write_text(e.listing(a,b))
# Dynamic PLT mapping for exact vold calls, not inferred function names.
with (S/'inputs/system__bin_vold').open('rb') as f:
 e=ELFFile(f);r=e.get_section_by_name('.rela.plt');sy=e.get_section_by_name('.dynsym');plt=e.get_section_by_name('.plt')
 mapping={hex(plt['sh_addr']+32+16*i):sy.get_symbol(rel['r_info_sym']).name for i,rel in enumerate(r.iter_relocations())}
(S/'evidence/vold-plt.json').write_text(json.dumps(mapping,indent=2)+'\n')
for name in ['footer-read','wipe-on-crypt-fail','key-location']:
 p=S/f'evidence/system__bin_vold-{name}.txt';t=p.read_text()
 for va,symbol in mapping.items():t=t.replace('#'+va+'\n','#'+va+' ; '+symbol+'\n')
 p.write_text(t)
