"""Artifact-specific check of the emitted RDMA bypass, using fetched ELF disassembly."""
from pathlib import Path
import gzip, hashlib, json, re, sys
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'source'))
import bootformat as b
E=R/'evidence'
linked=json.loads((E/'linked-capture.json').read_text())
build=json.loads((E/'build-receipt.json').read_text())
raw,_=b.ungzip((R/'artifacts/Image.gz-dtb').read_bytes())
assert b.sha(raw)==build['artifacts']['arch/arm64/boot/Image']['sha256']
mapraw=gzip.decompress((R/'artifacts/System.map.gz').read_bytes())
assert b.sha(mapraw)==build['artifacts']['System.map']['sha256']
syms={p[2]:int(p[0],16) for line in mapraw.decode().splitlines() if len(p:=line.split())==3}
dis=(E/'registration.disasm').read_text()
instructions={int(a,16):(word,op.strip()) for a,word,op in re.findall(r'^([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',dis,re.M)}
text=int(linked['Image']['text'],16)
for address,(word,op) in instructions.items():
 assert raw[address-text:address-text+4]==int(word,16).to_bytes(4,'little')
probe=syms['disp_probe']
def check(offset,pattern):
 op=instructions[probe+offset][1]
 assert re.search(pattern,op),(hex(offset),op,pattern)
 return dict(address=hex(probe+offset),instruction=op)
checks={}
checks['map_before_predicate']=check(0x2c4,r'<irq_of_parse_and_map>')
checks['irq_array_assignment']=check(0x2d4,r'str\s+w0, \[x20, x19, lsl #2\]')
checks['device_irq_assignment']=check(0x2d8,r'str\s+w0, \[x1, x2, lsl #2\]')
checks['OVL_bound']=check(0x2e8,r'cmp\s+x19, #0x1')
checks['branch_to_RDMA_test']=check(0x2ec,rf'b.hi\s+{probe+0x330:x}')
checks['RDMA_subtract_two']=check(0x330,r'sub\s+w0, w19, #0x2')
checks['RDMA_range_one']=check(0x334,r'cmp\s+w0, #0x1')
checks['non_RDMA_skip_log']=check(0x338,rf'b.hi\s+{probe+0x318:x}')
checks['name_lookup']=check(0x340,r'<ddp_get_reg_module_name>')
checks['mapped_IRQ_log_argument']=check(0x344,r'ldr\s+w3, \[x20, x19, lsl #2\]')
checks['log_format_page']=check(0x358,r'adrp\s+x0, ffffff8008df7000')
checks['log_format_offset']=check(0x35c,r'add\s+x0, x0, #0x688')
checks['one_log']=check(0x360,r'<printk>')
checks['log_to_loop']=check(0x368,rf'tbz\s+w0, #18, {probe+0x328:x}')
checks['loop_next']=check(0x328,r'add\s+x19, x19, #0x1')
checks['loop_back']=check(0x32c,rf'b\s+{probe+0xbc:x}')
checks['dynamic_debug_path_to_loop']=check(0x3b4,rf'b\s+{probe+0x14c:x}')
checks['shared_request']=check(0x30c,r'<request_threaded_irq>')
assert syms['disp_irq_handler']==0xffffff8008694f50
fmt=b'\x015ASUS49-DIAG headless RDMA IRQ registration skipped module=%d name=%s linux_irq=%u\n\0'
fmtaddr=0xffffff8008df7688
assert raw[fmtaddr-text:fmtaddr-text+len(fmt)]==fmt
legacy=dis.split('<disp_init_irq>:',1)[1].split('file format',1)[0]
assert not re.search(r'<(?:disp_register_dev_irq|request_threaded_irq)>',legacy)
source=(R/'source/base/drivers/misc/mediatek/video/mt8163/dispsys/ddp_irq.c').read_text()
assert '#if 0 /* irq mapped in DT probe() */' in source
result=dict(status='PASS',ELF_sha256=build['artifacts']['vmlinux']['sha256'],raw_Image_sha256=b.sha(raw),all_scoped_disassembly_words_match_compiled_Image=True,checks=checks,interpretation='For module indices 2 and 3, unsigned (module-2)<=1 reaches one name/array-based log, then either next-loop path (including existing dynamic debug) bypasses the sole probe request. OVL0/1, AAL7 and mutex13/DSI14 retain shared request paths. CONFIG17 remains its unchanged original predicate value and original outer mapping condition.',log_format=fmt[2:-1].decode(),legacy='CONFIG_OF=y; actual #if 0 block, not !CONFIG_OF; linked disp_init_irq contains no registration call; disp_register_dev_irq remains defined but scoped source has no active caller',other_scoped_requests='Both videox/primary_display.c requests use DSI_TE_1-eint and _esd_check_ext_te_irq_handler, not RDMA. See remote-extra.json.',runtime_registration_receipt=False,physical_GO=False)
(E/'registration-branch-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','ELF_sha256','all_scoped_disassembly_words_match_compiled_Image','log_format','runtime_registration_receipt']},indent=2))
