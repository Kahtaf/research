"""Inspect only pinned public shipped kernel and public reference source."""
from pathlib import Path
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]; WORK=ROOT.parent
sys.path.insert(0,str(ROOT/'source'))
sys.path.insert(0,str(WORK/'2026-11-07-asus-stock-kernel-version-control/source'))
import bootformat as b
from kallsyms import decode
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
stock=(WORK/'2026-11-07-asus-stock-kernel-version-control/artifacts/original.img').read_bytes()
assert hashlib.sha256(stock).hexdigest()=='f0bf4834a2d3ec207590c6742d0adb4fd9a3adc9a2dab5d0ec7c28f27963b140'
_,k,_,_=b.parse_image(stock); raw,_=b.ungzip(k[512:])
symbols,sym,base,addresses=decode(raw)
md=Cs(CS_ARCH_ARM64,CS_MODE_ARM); lines=[]; facts={}
names=['iManufacturer_store','iProduct_store','iSerial_store','functions_store','enable_store','fsg_store_ro','fsg_store_nofua','fsg_store_file','mass_storage_function_init','idVendor_store','idProduct_store','fsg_config_from_params','fsg_lun_open','fsg_sysfs_update']
for name in names:
 addr=sym[name]; off=addr-base; end=min(v for v in addresses if v>addr); data=raw[off:off+end-addr]
 facts[name]=dict(address=hex(addr),offset=off,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
 lines.append('FUNCTION '+name)
 for ins in md.disasm(data,addr):
  note=''
  if ins.mnemonic in ('bl','b') and ins.op_str.startswith('#'):
   target=int(ins.op_str[1:],16); note=' ; '+next((n for a,n in symbols if a==target),'?')
  lines.append(f'{ins.address:016x} {ins.bytes.hex()} {ins.mnemonic} {ins.op_str}{note}')
 lines.append('')
(ROOT/'evidence/shipped-attribute-contract.disasm').write_text('\n'.join(lines)+'\n')
(ROOT/'evidence/shipped-attribute-symbols.json').write_text(json.dumps(facts,indent=2)+'\n')
print('Contract disassembly retained; symbols:', len(facts))
