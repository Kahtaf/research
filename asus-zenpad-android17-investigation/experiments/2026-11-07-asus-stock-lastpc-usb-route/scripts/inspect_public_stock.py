"""Offline inspection of explicitly public original.img; outputs only to this spike."""
from pathlib import Path
import bisect, hashlib, importlib.util, json, struct as S, sys, zlib
sys.dont_write_bytecode = True
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
R=Path(__file__).resolve().parents[1]; W=R.parent
p=W/'2026-11-07-asus-stock-kernel-version-control/artifacts/original.img'
b=p.read_bytes(); sha=lambda b:hashlib.sha256(b).hexdigest()
assert b[:8]==b'ANDROID!'
ks=S.unpack_from('<I',b,8)[0]; page=S.unpack_from('<I',b,36)[0]
k=b[page:page+ks]; assert k[:4]==bytes.fromhex('88168858')
d=zlib.decompressobj(31); raw=d.decompress(k[512:]); fdt=d.unused_data
assert sha(raw)=='db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a'
parser=W/'2026-11-07-asus-stock-kernel-version-control/source/kallsyms.py'
spec=importlib.util.spec_from_file_location('stock_kallsyms',parser); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
symbols,sym,base,addresses=mod.decode(raw); rev={a:n for a,n in symbols}
names={'lastpc_dump_show','lastpc_dump','lastpc_plt_dump','mt_reg_dump','lastpc_init','lastpc_start','lastpc_probe','lastpc_plt_start','aee_rr_show_last_pc','aee_rr_reboot_reason_show','aee_rr_reboot_reason_proc_open','aee_rr_proc_init'}
md=Cs(CS_ARCH_ARM64,CS_MODE_ARM); facts=[]; lines=[]
for addr,name in symbols:
 if name not in names: continue
 end=addresses[bisect.bisect_right(addresses,addr)]; code=raw[addr-base:end-base]
 facts.append(dict(name=name,address=hex(addr),image_offset=addr-base,bytes=len(code),sha256=sha(code)))
 lines.append(f'FUNCTION {name} {addr:#x} bytes={len(code)}')
 for ins in md.disasm(code,addr):
  note=''
  if ins.mnemonic in ('bl','b') and ins.op_str.startswith('#'): note=' ; '+rev.get(int(ins.op_str[1:],16),'?')
  lines.append(f'{ins.address:016x} {ins.bytes.hex()} {ins.mnemonic} {ins.op_str}{note}')
 lines.append('')
# Include compiled DT nodes matching MCUCFG/lastpc, without exporting an image.
audit=W/'2026-11-06-asus-stock-initrd-size-premise/scripts/audit.py'
import ast
text=audit.read_text(); tree=ast.parse(text)
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='dt_parse')
env={'S':S,'sha':sha,'align':lambda n,a:(n+a-1)//a*a}; exec(ast.get_source_segment(text,node),env)
_,props=env['dt_parse'](fdt)
dt={f'{node}:{key}':value.hex() for (node,key),value in props.items() if 'lastpc' in node or 'mcucfg' in node}
# Locate compiled callback table for the RAM-console reboot-reason output.
# KALLSYMS_ALL is absent: identify raw contiguous function pointers instead of naming arbitrary data.
seq=S.pack('<QQQQ',sym['aee_rr_show_wdt_status'],sym['aee_rr_show_fiq_step'],sym['aee_rr_show_exp_type'],sym['aee_rr_show_last_pc'])
occ=[i for i in range(len(raw)) if raw.startswith(seq,i)]
summary={'input':str(p.relative_to(W)),'input_bytes':len(b),'input_sha256':sha(b),'wrapped_kernel_sha256':sha(k),'Image_sha256':sha(raw),'fdt_sha256':sha(fdt),'decoder':str(parser.relative_to(W)),'decoder_sha256':sha(parser.read_bytes()),'dt_parser':str(audit.relative_to(W)),'dt_parser_sha256':sha(audit.read_bytes()),'functions':facts,'compiled_dt':dt,'rr_callback_prefix_matches':[{'image_offset':i,'address':hex(base+i)} for i in occ]}
(R/'evidence/stock-lastpc.json').write_text(json.dumps(summary,indent=2)+'\n')
(R/'evidence/stock-lastpc.disasm').write_text('\n'.join(lines)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('functions',)},indent=2))
print('\n'.join(f"{x['name']} {x['address']} bytes={x['bytes']}" for x in facts))
