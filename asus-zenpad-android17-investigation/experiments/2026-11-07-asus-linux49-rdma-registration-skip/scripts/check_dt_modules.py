"""Report actual compiled-DT compatible matches; no runtime IRQ claims."""
from pathlib import Path
import json, re, struct, sys
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'source'))
import bootformat as b, fdt
B=R.parent/'2026-11-07-asus-linux49-retained-clock-capture'
_,dt=b.ungzip((B/'artifacts/Image.gz-dtb').read_bytes())
_,nodes,_=fdt.parse(dt)
D='drivers/misc/mediatek/video/mt8163/dispsys/'
s=(R/'source/base'/D/'ddp_drv.c').read_text()
body=re.search(r'const char \*ddp_reg_name_spy\(.*?\n\}',s,re.S).group()
enum=re.search(r'enum DISP_REG_ENUM \{(.*?)\n\};',(R/'source/base'/D/'ddp_hal.h').read_text(),re.S).group(1)
names=[n.strip() for n in enum.split(',') if n.strip()]
matches=[]
for module,compat in re.findall(r'case (DISP_\w+):\s*return "([^"]+)";',body):
 for path,props in nodes.items():
  if compat.encode() in props.get('compatible',b'').split(b'\0'):
   ints=props.get('interrupts',b'')
   matches.append(dict(module=module,index=names.index(module),compatible=compat,node=path,status=props.get('status',b'okay').rstrip(b'\0').decode(),interrupt_cells=list(struct.unpack('>'+str(len(ints)//4)+'I',ints)),diagnostic_skip=module in ['DISP_REG_RDMA0','DISP_REG_RDMA1']))
skips=[m for m in matches if m['diagnostic_skip']]
result=dict(compiled_DTB_sha256=b.sha(dt),present_display_modules=matches,expected_skip_line_count=len(skips),expected_skip_lines=[f"ASUS49-DIAG headless RDMA IRQ registration skipped module={m['index']} name=rdma{m['index']-2} linux_irq=<mapped Linux IRQ>" for m in skips],missing_RDMA_modules=[m for m in ['DISP_REG_RDMA0','DISP_REG_RDMA1'] if m not in [n['module'] for n in skips]],Linux_IRQ_numbers='Not observed; printed from existing dispsys_irq[] mapping at runtime. DT interrupt cells are not a registration receipt.',DT_status_limit='of_find_compatible_node ignores availability; status alone is not this control',runtime_registration_receipt=False)
(R/'evidence/compiled-dt-modules.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
