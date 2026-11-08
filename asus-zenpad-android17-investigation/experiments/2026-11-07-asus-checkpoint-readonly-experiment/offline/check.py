from pathlib import Path
import sys,struct as S,zlib,hashlib,importlib.util,bisect,json
sys.dont_write_bytecode=True
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
W=Path(__file__).resolve().parents[2]; O=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def module(p,n):
 s=importlib.util.spec_from_file_location(n,W/p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
pins={}
def read(p):
 b=(W/p).read_bytes();pins[p]=sha(b);return b
def unpack(b):
 ks=S.unpack_from('<I',b,8)[0];page=S.unpack_from('<I',b,36)[0];k=b[page:page+ks];assert k[:4]==bytes.fromhex('88168858');d=zlib.decompressobj(31);raw=d.decompress(k[512:]);return raw,d.unused_data
stock='2026-11-07-asus-stock-kernel-version-control/'
b=read(stock+'artifacts/original.img');assert sha(b)=='f0bf4834a2d3ec207590c6742d0adb4fd9a3adc9a2dab5d0ec7c28f27963b140'
raw,dt=unpack(b);assert sha(raw)=='db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a';pins['stock raw Image']=sha(raw)
p=stock+'source/kallsyms.py';read(p);m=module(p,'ks');symbols,sym,base,addresses=m.decode(raw);rev={a:n for a,n in symbols};md=Cs(CS_ARCH_ARM64,CS_MODE_ARM);lines=[]
for name in ['aee_rr_show_fiq_step','aee_rr_rec_fiq_step','aee_rr_curr_fiq_step','aee_rr_last_fiq_step','ram_console_init','ram_console_save_old','ram_console_early_init','ram_console_late_init','ram_console_driver_probe']:
 a=sym.get(name)
 if a is None:lines.append(name+' SYMBOL ABSENT');continue
 e=addresses[bisect.bisect_right(addresses,a)];code=raw[a-base:e-base];lines.append(f'{name} {a:#x} image_offset={a-base:#x} bytes={len(code)} sha256={sha(code)}')
 for ins in md.disasm(code,a):
  note=''
  if ins.mnemonic in ('bl','b') and ins.op_str.startswith('#'):note=' ; '+rev.get(int(ins.op_str[1:],16),'?')
  lines.append(f'{ins.address:016x} {ins.bytes.hex()} {ins.mnemonic} {ins.op_str}{note}')
lines.append('RAM_CONSOLE_SYMBOLS '+str([(hex(a),n) for a,n in symbols if 'ram_console' in n]))
lines.append('FORMAT '+repr(raw[0xffffffc000e37a38-base:0xffffffc000e37a38-base+32]))
(O/'stock-fiq.disasm').write_text('\n'.join(lines)+'\n')
pkg='2026-11-07-asus-linux49-failure-log-package/'
b=read(pkg+'artifacts/candidate.img');assert sha(b)=='cc367b543eebea476b15a9033648c9547e48c7ac02d8c42856b372623bffb265';r,dt=unpack(b);pins['latest4.9 raw Image']=sha(r);pins['latest4.9 appended DT']=sha(dt)
p=pkg+'source/fdt.py';read(p);f=module(p,'fd');h,nodes,t=f.parse(dt)
selected={n:{k:v.hex() for k,v in props.items()} for n,props in nodes.items() if n=='' or n=='/reserved-memory' or n.startswith('/reserved-memory/')}
(O/'latest49-dt.json').write_text(json.dumps(selected,indent=2)+'\n')
base=0x44400000;end=base+0x80000;overlaps=[]
for n,props in nodes.items():
 if not n.startswith('/reserved-memory/'):continue
 reg=props.get('reg',b'')
 for off in range(0,len(reg),16):
  if len(reg)%16:break
  a,size=S.unpack_from('>QQ',reg,off)
  if size and a<end and a+size>base:overlaps.append({'node':n,'base':hex(a),'size':hex(size),'props':{k:v.hex() for k,v in props.items()}})
read(pkg+'artifacts/resolved.config');read(pkg+'evidence/packaging-receipt.json')
read('2026-11-07-asus-usb-retained-log-initialization/source/arch/arm64/kernel/asus_retained_trace.c')
read('2026-11-07-asus-early-watchdog-handoff/evidence/RECEIPT.json')
read('2026-11-07-asus-usb-retained-log-initialization/evidence/source-pins.json')
read('2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18/drivers/misc/mediatek/ram_console/mtk_ram_console.c')
(O/'evidence.json').write_text(json.dumps({'pins':pins,'overlaps':overlaps,'root_compatible':nodes[''].get('compatible',b'').decode().split('\0')},indent=2)+'\n')
print(json.dumps({'pins':pins,'overlaps':overlaps},indent=2))
