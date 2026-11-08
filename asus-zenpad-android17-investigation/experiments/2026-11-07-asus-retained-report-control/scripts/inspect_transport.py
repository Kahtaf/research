from pathlib import Path
import hashlib,json,struct,sys
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent
sys.path.insert(0,str(R/'source'))
import bootformat as b
from kallsyms import decode
working=(W/'2026-11-07-asus-stock-kernel-sd-control/artifacts/candidate.img').read_bytes()
assert b.sha(working)=='eccfc87f28169bee14d0675f6ad31335f832ab25db46b013b03a06109b0df13d'
_,k,_,_=b.parse_image(working);raw,dt=b.ungzip(k[512:]);symbols,sym,base,addrs=decode(raw)
rev={v:k for k,v in sym.items()};md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
selected=['devkmsg_write','do_syslog','console_unlock','console_unlock.part.15','call_console_drivers.constprop.24','ram_console_write','sram_log_save','ram_console_early_init','ram_console_show','memory_open','chr_dev_init']
lines=[];facts={}
for name in selected:
 addr=sym[name];end=min(a for a in addrs if a>addr);data=raw[addr-base:end-base]
 facts[name]=dict(address=hex(addr),bytes=len(data),sha256=b.sha(data))
 lines.append('\nFUNCTION '+name+' '+hex(addr))
 for i in md.disasm(data,addr):
  note=''
  if i.mnemonic in ('bl','b') and i.op_str.startswith('#'):note=' ; '+rev.get(int(i.op_str[1:],16),'?')
  lines.append(f'{i.address:016x} {i.bytes.hex()} {i.mnemonic} {i.op_str}{note}')
# Exact registered console: write pointer at +16, flags at +64.
con=0xffffffc001002c28;co=con-base
assert raw[co:co+4]==b'ram\0'
assert struct.unpack_from('<Q',raw,co+16)[0]==sym['ram_console_write']
flags=struct.unpack_from('<H',raw,co+64)[0];assert flags==21
# memory_open decodes minor using a 32-byte memdevs entry at this exact address.
memdevs=0xffffffc000b38378;entry=memdevs+11*32
nameptr=struct.unpack_from('<Q',raw,entry-base)[0]
assert raw[nameptr-base:nameptr-base+5]==b'kmsg\0'
fops=struct.unpack_from('<Q',raw,entry-base+16)[0]
assert struct.unpack_from('<Q',raw,fops-base+56)[0]==sym['devkmsg_write']
facts['kmsg_binding']=dict(major=1,minor=11,memdevs=hex(memdevs),entry=hex(entry),fops=hex(fops),write_iter_offset=56,write_iter=hex(sym['devkmsg_write']))
facts['ram_console']=dict(address=hex(con),name='ram',write=hex(sym['ram_console_write']),flags=flags,CON_ENABLED=True,CON_ANYTIME=True,CON_CONSDEV=bool(flags & 2))
facts['input']=dict(working_sha256=b.sha(working),kernel_sha256=b.sha(k),raw_sha256=b.sha(raw),fdt_sha256=b.sha(dt))
(R/'evidence/stock-transport.disasm').write_text('\n'.join(lines)+'\n')
(R/'evidence/stock-transport.json').write_text(json.dumps(facts,indent=2)+'\n')
print(json.dumps(facts,indent=2))
