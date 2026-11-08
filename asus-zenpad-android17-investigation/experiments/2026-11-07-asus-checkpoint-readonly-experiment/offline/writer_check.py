from pathlib import Path
import sys,struct as S,zlib,hashlib,importlib.util,bisect,json
sys.dont_write_bytecode=True
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest()
p=W/'2026-11-07-asus-stock-kernel-version-control/artifacts/original.img';b=p.read_bytes();assert sha(b)=='f0bf4834a2d3ec207590c6742d0adb4fd9a3adc9a2dab5d0ec7c28f27963b140';ks=S.unpack_from('<I',b,8)[0];page=S.unpack_from('<I',b,36)[0];raw=zlib.decompress(b[page+512:page+ks],31);assert sha(raw)=='db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a'
p=W/'2026-11-07-asus-stock-kernel-version-control/source/kallsyms.py';s=importlib.util.spec_from_file_location('ks',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);symbols,sym,base,addresses=m.decode(raw);rev={a:n for a,n in symbols};md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
want=['aee_rr_rec_fiq_step','aee_rr_rec_reboot_mode','aee_rr_reboot_reason_proc_open','aee_rr_proc_init','kmsg_write','devkmsg_write','ram_console_write','ram_console_show','ram_console_file_open','aed_proc_debug_init','proc_generate_kernel_notify_write','mtk_wdt_restart','arch_reset','machine_restart','kernel_restart','sram_log_save','devkmsg_open','call_console_drivers','ram_console_late_init']
lines=[];found={}
for name in want:
 a=sym.get(name);found[name]=hex(a) if a else None
 if a is None:continue
 e=addresses[bisect.bisect_right(addresses,a)];code=raw[a-base:e-base];lines.append(f'FUNCTION {name} {a:#x} bytes={len(code)} sha256={sha(code)}')
 for ins in md.disasm(code,a):
  note=''
  if ins.mnemonic in ('bl','b') and ins.op_str.startswith('#'):note=' ; '+rev.get(int(ins.op_str[1:],16),'?')
  lines.append(f'{ins.address:016x} {ins.bytes.hex()} {ins.mnemonic} {ins.op_str}{note}')
callers={n:[] for n in ['aee_rr_rec_fiq_step','aee_rr_rec_reboot_mode']}
# Scan aligned Image words only for direct branch/link instructions targeting those exact symbols.
for off in range(0,len(raw)-3,4):
 v=S.unpack_from('<I',raw,off)[0]
 if v&0x7c000000!=0x14000000:continue
 imm=v&0x3ffffff;imm=imm-(1<<26) if imm&(1<<25) else imm;dest=base+off+imm*4
 for n,entries in callers.items():
  if dest==sym[n]:
   j=bisect.bisect_right(addresses,base+off)-1;entries.append({'instruction':hex(base+off),'owner':symbols[j][1],'owner_offset':hex(base+off-addresses[j]),'branch_link':bool(v&0x80000000)})
(O/'writer-abi.disasm').write_text('\n'.join(lines)+'\n')
sources={}
root=W/'2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18'
for rel in ['drivers/misc/mediatek/ram_console/mtk_ram_console.c','drivers/misc/mediatek/aee/common/reboot-reason.c','drivers/misc/mediatek/aee/aed/aed-debug.c','drivers/misc/mediatek/aee/aed/aed-main.c','kernel/printk/printk.c','drivers/char/mem.c']:
 sources[str(root/rel)]=sha((root/rel).read_bytes())
(O/'writer-source-pins.json').write_text(json.dumps(sources,indent=2)+'\n')
(O/'writer-abi.json').write_text(json.dumps({'stock_Image_sha256':sha(raw),'symbols':found,'direct_callers':callers,'note':'Aligned-word scan may include data false positives; owner names and relevant source used to classify. Indirect calls are not excluded.'},indent=2)+'\n')
print(json.dumps({'symbols':found,'direct_callers':callers},indent=2))
