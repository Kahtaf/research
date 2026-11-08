from pathlib import Path
import sys,hashlib
sys.dont_write_bytecode=True
W=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(W/'2026-11-07-asus-stock-kernel-version-control/source'))
import bootformat as b,kallsyms
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
p=W/'2026-11-07-asus-stock-legacy-ram-usb-reporter/artifacts/candidate.img'
d=p.read_bytes();assert hashlib.sha256(d).hexdigest()=='dc0b98e66798e3abc019f454921b1c84ff3ce58e356e26d0785e05b7714d3427'
h,k,r,t=b.parse_image(d);raw,dt=b.ungzip(k[512:]);assert b.sha(raw)=='db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a'
syms,sym,base,addrs=kallsyms.decode(raw)
md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
for key in ['printk','register_restart_handler','atomic_notifier_call_chain']:
 print('SYMBOL',key,hex(sym[key]))
for name in ['kernel_restart','do_kernel_restart','mtk_arch_reset_init','mtk_arch_reset_handle','mtk_wdt_restart','aee_rr_rec_fiq_step']:
 if name not in sym: print('MISSING',name);continue
 a=sym[name];end=next(x for x in addrs if x>a)
 print('\n',name,hex(a),hex(end))
 for ins in md.disasm(raw[a-base:end-base],a):
  print(hex(ins.address),ins.bytes.hex(),ins.mnemonic,ins.op_str)
