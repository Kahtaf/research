from pathlib import Path
import sys,struct,json
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1]; W=R.parent
sys.path.insert(0,str(W/'2026-11-07-asus-stock-kernel-version-control/source'))
import bootformat as b,kallsyms
from capstone import *
_,k,_,_=b.parse_image((W/'2026-11-07-asus-stock-legacy-ram-usb-reporter/artifacts/candidate.img').read_bytes());raw,dt=b.ungzip(k[512:]);ss,s,base,aa=kallsyms.decode(raw)
cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
output=[]
for a,e in [(base+0x200,base+0x260),(base+0x1770,base+0x179c),(s['aee_rr_show_idvfs_ctrl_reg'],s['aee_rr_show_idvfs_enable_cnt']),(s['aee_rr_reboot_reason_show'],next(x for x in aa if x>s['aee_rr_reboot_reason_show']))]:
 for i in cs.disasm(raw[a-base:e-base],a):output.append(f'{i.address:#x} {i.bytes.hex()} {i.mnemonic} {i.op_str}')
output+=['LITERAL '+hex(base+o)+' '+hex(struct.unpack_from('<Q',raw,o)[0]) for o in range(0x210,0x258,8)]
(R/'evidence/placement-inspect.disasm').write_text('\n'.join(output)+'\n')
slot=s['aee_rr_show_idvfs_ctrl_reg']; ptr=struct.pack('<Q',slot)
print('\n'.join(output));print('slot pointers',[hex(base+i) for i in range(0,len(raw)-7,8) if raw[i:i+8]==ptr]); print('symbols surrounding append',[(hex(a),n) for a,n in ss if base+len(raw)-128<=a<=base+len(raw)+256])
