from pathlib import Path
import sys,json,uuid,shutil,re
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];P=R.parent/'2026-11-07-asus-stock-entry-writer-control-r2'
assert not (R/'source/entry.S').exists()
for n in ['asus_entry_tag.h','stock-marker-only.dtb','bootformat.py','install.py','legacy_adb.py','adb','plan_only.py']:
 shutil.copyfile(P/'source'/n,R/'source'/n)
shutil.copyfile(P/'qa/fixture-runtime-memory.dtb',R/'qa/fixture-runtime-memory.dtb')
run=str(uuid.uuid4());(R/'evidence/identity.json').write_text(json.dumps(dict(run_uuid=run),indent=2)+'\n')
src=(P/'source/asus_entry_text.S').read_text();out=[];sites=[]
for line_no,line in enumerate(src.splitlines(True),1):
 if '.Laet_done' in line and not line.lstrip().startswith(('.', '*')):
  m=re.match(r'(\s*)(b\.\w+|cbz|cbnz|tbz|tbnz)\s+(.*?)\.Laet_done(.*)',line)
  assert m,line
  pre,op,args,tail=m.groups();args=args.rstrip().rstrip(',');ops=[a.strip() for a in args.split(',')] if args else []
  ops+=['']*(2-len(ops));out.append(f'{pre}diag_refuse {op}, {ops[0]}, {ops[1]}, {line_no}{tail}\n');sites.append(dict(line=line_no,original=line.strip()))
 else: out.append(line)
src=''.join(out)
assert src.count('.Laet_done')==1
# Fallthrough success alone reaches this injected success marker; all refusals use private stubs.
src=src.replace('.Laet_done:', '\tmov x5, #0xffff\n\tb diag_finish\n.Laet_done:')
(R/'source/asus_entry_text.S').write_text(src)
(R/'evidence/source-sites.json').write_text(json.dumps(sites,indent=2)+'\n')
(R/'source/entry.S').write_text(r'''.macro adr_l dst, sym
 adrp \dst, \sym
 add \dst, \dst, :lo12:\sym
.endm
.set next_fail,0
.macro diag_refuse op, a1, a2, line
 .set next_fail,next_fail+1
 .global diag_id_\@,diag_line_\@,diag_fail_\@
 .equ diag_id_\@,next_fail
 .equ diag_line_\@,\line
 .ifb \a1
  \op diag_fail_\@
 .else
  .ifb \a2
   \op \a1,diag_fail_\@
  .else
   \op \a1,\a2,diag_fail_\@
  .endif
 .endif
 .pushsection .diagfail,"ax"
diag_fail_\@:
 mov x5,#next_fail
 b diag_finish
 .popsection
.endm
.section .entry,"ax"
.global capture_entry
capture_entry:
 adr_l x4,own_record
 str x0,[x4,#8]
 mrs x5,CurrentEL
 str x5,[x4,#16]
 mov x6,#-1
 cmp x5,#4
 b.eq 1f
 cmp x5,#8
 b.ne 2f
 mrs x6,sctlr_el2
 b 2f
1:
 mrs x6,sctlr_el1
2:
 str x6,[x4,#24]
 str xzr,[x4,#32]
 movz x7,#0x454e
 movk x7,#0x5452,lsl #16
 movk x7,#0x5953,lsl #32
 movk x7,#0x4545,lsl #48
 str x7,[x4]
 dsb sy
#include "asus_entry_text.S"
.section .diagfinish,"ax"
diag_finish:
 adr_l x4,own_record
 str x5,[x4,#32]
 dsb sy
 // Only the 40-byte own-Image record. 16-byte stride covers all ARMv8
 // minimum D-cache line sizes, without reading CTR_EL0 or touching a new VA.
 dc cvac,x4
 add x6,x4,#16
 dc cvac,x6
 add x6,x4,#32
 dc cvac,x6
 dsb sy
 b stock_stext
''')
(R/'source/readback.S').write_text('''.section .readback,"ax"
.global readback
readback:
 stp x29,x30,[sp,#-48]!
 mov x29,sp
 stp x0,x1,[sp,#16]
 str x2,[sp,#32]
 adrp x6,own_record
 add x6,x6,:lo12:own_record
 ldp x1,x2,[x6]
 ldp x3,x4,[x6,#16]
 ldr x5,[x6,#32]
 adr x0,format
 bl stock_printk
 ldp x0,x1,[sp,#16]
 ldr x2,[sp,#32]
 bl stock_memset
 ldp x29,x30,[sp],#48
 ret
format:
 .asciz "\\0011ASUS-ENTRY-DIAG '''+run+''' magic=%016llx x0=%016llx el=%llx sctlr=%016llx status=%llx\\n"
.section .record,"aw"
.global own_record,own_record_end
own_record:
 .zero 40
own_record_end:
''')
ld=(P/'source/control.ld').read_text().replace('saved = 0xffffffc001278568;','')
ld=ld.replace('. = 0xffffffc000696b14; .readback : { *(.readback) }','.readback 0xffffffc000696b14 : { *(.readback) }\n .record 0xffffffc000696c40 : { *(.record) }')
ld=ld.replace('* (.entry)','* (.entry)')
ld=ld.replace('{ *(.entry) }','{ *(.entry) *(.diagfail) *(.diagfinish) }')
ld=ld.replace('<= 352','<= 300')+'\nASSERT(ADDR(.record)+SIZEOF(.record) <= 0xffffffc000696c74, "record overflow")\n'
(R/'source/control.ld').write_text(ld)
print(run)
