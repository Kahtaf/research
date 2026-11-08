"""Pinned public preparation only; no device/network/private inputs."""
from pathlib import Path
import sys,struct,json,uuid,shutil
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent
sys.path.insert(0,str(W/'2026-11-07-asus-stock-kernel-version-control/source'))
import bootformat as b,kallsyms
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
sys.path.insert(0,str(W/'2026-11-06-asus-full-boot-lk-contract/scripts'))
import fdt
assert not (R/'evidence/preparation.json').exists()
def boundary(event,args):
 if event=='open':assert not any(x in str(args[0]) for x in ('/private/','/device-backup/','root_shell_wifi.py','mtk-su-mirror-b','/dev/'))
 if event.startswith(('socket.','subprocess.')) or event in ('os.system','os.posix_spawn'):raise RuntimeError(event)
sys.addaudithook(boundary)
d=(W/'2026-11-07-asus-stock-legacy-ram-usb-reporter/artifacts/candidate.img').read_bytes();assert b.sha(d)=='dc0b98e66798e3abc019f454921b1c84ff3ce58e356e26d0785e05b7714d3427'
h,k,ram,t=b.parse_image(d);raw,dt=b.ungzip(k[512:]);assert not t and b.sha(raw)=='db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a'
ss,s,base,aa=kallsyms.decode(raw); assert base==0xffffffc000080000
cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
# Exact shipped literals, independent of source version or absent kallsyms data symbols.
assert struct.unpack_from('<Q',raw,0x228)[0]==base
end=struct.unpack_from('<Q',raw,0x230)[0]
bss_start,bss_stop=struct.unpack_from('<QQ',raw,0x240)
assert base+len(raw)==bss_start==0xffffffc0010ad7f0 and bss_stop==0xffffffc001330018
assert end==0xffffffc001335000 and struct.unpack_from('<Q',raw,16)[0]==end-base
switch=list(cs.disasm(raw[0x270:0x2c0],base+0x270))
assert [(i.mnemonic,i.op_str) for i in switch[:6]]==[('adr','x3, #0xffffffc000080240'),('ldp','x6, x7, [x3], #0x10'),('cmp','x6, x7'),('b.hs','#0xffffffc000080288'),('str','xzr, [x6], #8'),('b','#0xffffffc000080278')]
# Slot is ordinary mapped text, with one live callback-table pointer and one kallsyms address-table value.
slot=s['aee_rr_show_idvfs_ctrl_reg'];slot_end=next(x for x in aa if x>slot);assert slot_end-slot==352
ptrs=[base+i for i in range(0,len(raw)-7,8) if raw[i:i+8]==struct.pack('<Q',slot)]
assert ptrs==[0xffffffc000c0a948,0xffffffc001002ef8]
# Kallsyms address run contains this exact value and its adjacent symbols.
idx=aa.index(slot);assert struct.unpack_from('<3Q',raw,ptrs[0]-base-8)==tuple(aa[idx-1:idx+2])
refs=[]
for off in range(0,s['_etext']-base,4):
 word=struct.unpack_from('<I',raw,off)[0]
 if word&0x7c000000==0x14000000:
  imm=word&0x3ffffff;imm=imm-(1<<26) if imm&(1<<25) else imm;target=base+off+imm*4
  if slot<=target<slot_end and not slot<=base+off<slot_end:refs.append(hex(base+off))
assert refs==[],refs
# Actual DT: additive root marker only, every other token/property preserved.
fh,nodes,tokens=fdt.parse(dt);assert nodes['']['compatible']==b'mediatek,mt8163\0'
stream=bytearray();replacement=b'mediatek,mt8163\0asus,p00a\0'
for kind,path,name,value,old in tokens:
 if (kind,path,name)==(3,'','compatible'):
  old=old[:4]+struct.pack('>I',len(replacement))+old[8:12]+replacement;old+=bytes(-len(old)%4)
 stream+=old
nh=list(fh);delta=len(stream)-fh[9];nh[1]+=delta;nh[3]+=delta;nh[9]=len(stream)
actual_dt=struct.pack('>10I',*nh)+dt[40:fh[2]]+stream+dt[fh[3]:]
expected={p:dict(v) for p,v in nodes.items()};expected['']['compatible']=replacement
assert fdt.parse(actual_dt)[1]==expected
assert nodes['/memory@00000000']['reg']==bytes.fromhex('00000000400000000000000020000000')
# Fixture overlay uses only the public observed runtime reg, not a candidate DT change.
obs=(W/'2026-11-07-asus-runtime-memory-contract/evidence/observation.json').read_bytes()
admission=(W/'2026-11-07-asus-runtime-memory-contract/evidence/parent-runtime-admission.json').read_bytes();ad=json.loads(admission)
assert ad['matches_R2_guard'] and ad['raw_hex']=='0000000040000000000000007d600000'
fixture=bytearray(actual_dt);hits=[]
for pos in range(0,len(fixture)-15,4):
 if fixture[pos:pos+16]==nodes['/memory@00000000']['reg']:hits.append(pos)
assert len(hits)==1;fixture[hits[0]:hits[0]+16]=bytes.fromhex(ad['raw_hex'])
fexpect={p:dict(v) for p,v in expected.items()};fexpect['/memory@00000000']['reg']=bytes.fromhex(ad['raw_hex']);assert fdt.parse(fixture)[1]==fexpect
(R/'source/stock-marker-only.dtb').write_bytes(actual_dt);(R/'qa/fixture-runtime-memory.dtb').write_bytes(fixture)
(R/'evidence/parent-runtime-admission.json').write_bytes(admission);(R/'evidence/observation.json').write_bytes(obs)
asm=(W/'2026-11-07-asus-entry-checkpoint-dt-guard-fix/source/arch/arm64/kernel/asus_entry_text.S').read_bytes();assert b.sha(asm)=='32f22ec90acd2fc6787a15589ada5c2a1d06117768b43cc8ab88051c11cbfc5a'
(R/'source/asus_entry_text.S').write_bytes(asm)
run=str(uuid.uuid4());tag=f'ASUS49-ENTRY run={run} stage=stext-preargs stock-control=R2 donor={b.sha(d)} writer={b.sha(asm)}\n'
(R/'source/asus_entry_tag.h').write_text('#define ASUS_ENTRY_TAG '+json.dumps(tag)+'\n#define ASUS_ENTRY_TAG_LEN '+str(len(tag))+'\n')
(R/'source/entry.S').write_text('''.macro adr_l dst, sym
 adrp \\dst, \\sym
 add \\dst, \\dst, :lo12:\\sym
.endm
.section .entry,"ax"
#include "asus_entry_text.S"
 b stock_stext
''')
(R/'source/readback.S').write_text('''#include "asus_entry_tag.h"
.section .readback,"ax"
.global readback
readback:
 stp x29,x30,[sp,#-48]!
 mov x29,sp
 stp x0,x1,[sp,#16]
 str x2,[sp,#32]
 adrp x3,saved
 ldr x3,[x3,:lo12:saved]
 cbz x3,clear
 ldr w4,[x3,#0x30]
 cmp w4,#0x400
 b.lo clear
 mov w5,#0x80000
 cmp w4,w5
 b.hs clear
 sub w5,w5,w4
 ldr w1,[x3,#0x38]
 cbz w1,clear
 cmp w1,w5
 b.hi clear
 ldr w6,[x3,#0x34]
 cbnz w6,clear
 mov w6,#ASUS_ENTRY_TAG_LEN
 cmp w1,w6
 csel w1,w1,w6,lo
 add x2,x3,w4,uxtw
 adr x0,format
 bl stock_printk
clear:
 ldp x0,x1,[sp,#16]
 ldr x2,[sp,#32]
 bl stock_memset
 ldp x29,x30,[sp],#48
 ret
format:
 .asciz "\\0011%.*s"
''')
(R/'source/control.ld').write_text(f'''_text = {base:#x};
_end = {end:#x};
stock_stext = {base+64:#x};
stock_printk = {s['printk']:#x};
stock_memset = {s['__memset_io']:#x};
saved = 0xffffffc001278568;
SECTIONS {{
 . = {slot:#x}; .readback : {{ *(.readback) }}
 . = {bss_start:#x}; .entry : {{ *(.entry) }}
 .init.rodata : {{ *(.init.rodata) }}
 /DISCARD/ : {{ *(.comment) *(.note*) }}
}}
ASSERT(SIZEOF(.readback) <= 352, "readback slot overflow")
ASSERT(. < {bss_stop:#x}, "entry exceeds BSS")
''')
listing=lambda blob,pc:''.join(f'{i.address:#x} {i.bytes.hex()} {i.mnemonic} {i.op_str}\n' for i in cs.disasm(blob,pc))
(R/'evidence/stock-bss-clear.disasm').write_text(listing(raw[0x238:0x270],base+0x238)+listing(raw[0x270:0x2c0],base+0x270))
(R/'evidence/slot-original.disasm').write_text(listing(raw[slot-base:slot_end-base],slot))
receipt=dict(run_uuid=run,tag=tag,tag_bytes=len(tag),base=hex(base),end=hex(end),bss_start=hex(bss_start),bss_stop=hex(bss_stop),slot=hex(slot),slot_end=hex(slot_end),slot_pointer_locations=list(map(hex,ptrs)),external_direct_branches_into_slot=refs,original_header_size=end-base,raw_bytes=len(raw),writer_sha256=b.sha(asm),candidate_memory_unchanged=True,fixture_overlay_only=ad,actual_dt_sha256=b.sha(actual_dt),fixture_dt_sha256=b.sha(fixture))
(R/'evidence/preparation.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
