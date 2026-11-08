"""Scoped reachability and read-to-read/return paths of the actual linked delay."""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1];E=R/'evidence'
text=(E/'delay-loop.disasm').read_text();section=text.split('<__delay>:',1)[1].split('\n\n\n',1)[0]
ins={int(m[1],16):(m[2],m[3].split('//')[0].strip()) for m in re.finditer(r'^([0-9a-f]+):[ \t]+[0-9a-f]+[ \t]+(\S+)[ \t]*(.*)$',section,re.M)}
assert ins
entry=min(ins);selector=next(a for a,(op,args) in ins.items() if op=='cbnz' and args.startswith('x0,'))
assert '<asus_capture_delay_begin>' in ins[selector-4][1]
selected=int(ins[selector][1].split(',')[1].split()[0],16);unselected=selector+4
assert ins[selected]==('mov','x22, x0')
# x22 is the callee-saved nonzero cookie on the selected route, until epilogue.
def successors(a,sel):
 op,args=ins[a]
 if op=='ret':return []
 if op=='b':return [int(args.split()[0],16)]
 if op.startswith('b.'):return [a+4,int(args.split()[0],16)]
 if op in ['cbz','cbnz']:
  reg,dest=args.split(',',1);t=int(dest.split()[0],16)
  if reg=='x22' and sel:return [a+4] if op=='cbz' else [t]
  return [a+4,t]
 return [a+4]
def reachable(start,sel):
 seen=set();todo=[start]
 while todo:
  a=todo.pop()
  if a in seen:continue
  assert a in ins,hex(a);seen.add(a);todo.extend(successors(a,sel))
 return seen
s=reachable(selected,True);v=reachable(unselected,False)
physical=lambda a:ins[a][0]=='mrs' and 'cntpct_el0' in ins[a][1]
virtual=lambda a:ins[a][0]=='mrs' and 'cntvct_el0' in ins[a][1]
pct=sorted(a for a in s if physical(a));vct=sorted(a for a in v if virtual(a));ool=sorted(a for a in v if ins[a][0]=='blr')
assert len(pct)==3 and len(vct)==2 and len(ool)==2
assert not any(virtual(a) or ins[a][0]=='blr' for a in s)
assert not any(physical(a) or '<asus_capture_delay_point>' in ins[a][1] for a in v)
assert all(ins[a-4][0]=='isb' for a in pct)
assert all(ins[a][0]!='ldr' or not ins[a][1].startswith(('w0,','w1,')) for a in s),'selected no key load'
# The selected code has only callee-saved-cookie stores/restores, no key change.
assert [ins[a] for a in s if ins[a][0] in ['mov','add','sub'] and ins[a][1].startswith('x22,')]==[('mov','x22, x0')]
start=pct[0];loops=pct[1:]
assert ins[start][1]=='x23, cntpct_el0' and all(ins[a][1]=='x20, cntpct_el0' for a in loops)
# All finite read-to-next-read/RET paths: one YIELD for continuation, none for return.
# No instruction cycle is permitted between these real read boundaries.
paths=[]
def walk(a,path):
 if a in loops or ins[a][0]=='ret':
  paths.append((a,path));return
 assert a not in path,('cycle without read/return',hex(a))
 for z in successors(a,True):walk(z,path+[a])
for read in loops:
 before=len(paths);walk(read+4,[])
 for stop,path in paths[before:]:
  yields=sum(ins[a][0]=='yield' for a in path)
  assert yields==(1 if stop in loops else 0),(hex(read),hex(stop),yields)
  if stop in loops:assert sum(ins[a][0]=='isb' for a in path)==1
  assert not any(ins[a][0]=='mrs' for a in path)
  assert any(ins[a]==('sub','x0, x20, x23') for a in path)
  assert any(ins[a]==('cmp','x21, x0') for a in path)
# Unselected direct/OOL paths each retain ISB in original get_cycles route.
assert ins[unselected][0]=='isb'
assert all(any(ins[z][0]=='isb' for z in range(a-20,a,4) if z in ins) for a in vct)
# Scope __const_udelay actual arithmetic: normalize instruction addresses only.
base=json.loads((E/'base-disassembly.json').read_text())['__const_udelay']
def normalized(d):
 out=[]
 for m in re.finditer(r'^\s*[0-9a-f]+:[ \t]+[0-9a-f]+[ \t]+(\S+)[ \t]*(.*)$',d,re.M):
  op,args=m[1],m[2].split('//')[0].strip()
  if op in ['bl','b']:args=re.sub(r'^[0-9a-f]+ ', '',args)
  if op=='adrp':args=re.sub(r', [0-9a-f]+ ', ', ADDRESS ',args)
  out.append((op,args))
 return out
co=text.split('<__const_udelay>:',1)[1].split('\n\n\n',1)[0]
assert normalized(base)==normalized(co),'actual arithmetic/calc hook/cycles arg changed'
linked=json.loads((E/'linked-capture.json').read_text());identity=json.loads((E/'identity.json').read_text())
r=dict(status='PASS_ACTUAL_ELF_ROUTES',uuid=identity['run_uuid'],vmlinux_sha256=json.loads((E/'build-receipt.json').read_text())['artifacts']['vmlinux']['sha256'],delay_entry=entry,selector=selector,selected_entry=selected,unselected_entry=unselected,selected_read_domain=1,raw_physical_bypasses_virtual_OOL=True,selected_start_site=start,selected_condition_sites=loops,unselected_CNTVCT_sites=vct,unselected_virtual_OOL_calls=ool,selected_reachable_instructions=len(s),unselected_reachable_instructions=len(v),selected_read_boundary_paths=len(paths),one_ISB_per_read=True,one_YIELD_per_continuation=True,actual_const_arithmetic_and_hook_operands_unchanged=True,runtime_virtual_key='UNESTABLISHED; no historical inference',source_loop_restores_byte_exact=True,scope='actual __delay CFG, __const_udelay arithmetic, scoped recorder/source checks; no physical execution')
(E/'route-proof.json').write_text(json.dumps(r,indent=2)+'\n');linked['delay_read_routes']=r;(E/'linked-capture.json').write_text(json.dumps(linked,indent=2)+'\n')
def off(a):return '__delay+'+hex(a-entry)
(E/'route-proof.md').write_text(f'''# Actual selected read-route proof

Actual candidate ELF SHA256 `{r['vmlinux_sha256']}`; one successful j8 build. This is static branch proof, not physical permission proof.

The result of asus_capture_delay_begin is tested at {off(selector)}. Nonzero branches to {off(selected)} and saves the cookie in x22. Its first raw CNTPCT is {off(start)} into x23; condition reads are {', '.join(off(a) for a in loops)} into x20. Each has exactly one immediately preceding ISB. Reachability from the selected arm contains no CNTVCT MRS, BLR, or virtual-key load; x22 stays callee-saved/nonzero until epilogue. This proves bypass independent of the virtual key, rather than relying on a guessed activation.

Zero falls through {off(unselected)} to the original virtual route: direct CNTVCT sites {', '.join(off(a) for a in vct)} and OOL BLR sites {', '.join(off(a) for a in ool)}, selected by the original key branch. No physical read or selected milestone is reachable on that arm. Actual base ELF before editing had three CNTVCT sites and three virtual BLR sites; historical key activation is unestablished.

All {len(paths)} finite selected condition-read-to-next-read/RET CFG paths were checked. Continuation executes one YIELD and one ISB before the next actual read; return executes no YIELD. Sub x0,x20,x23 then cmp x21,x0 and unsigned b.ls/b.hi implement the unchanged unsigned relative comparison. The selected terminating value is passed to stage6 before the epilogue. Compiler duplication of the saturated iteration tail adds static read/YIELD sites, not dynamic reads or an iteration cap. Source loop, saturation, milestones and return order restore byte-exact after reversing two read call substitutions; host controls exercise actual bodies. Normalized actual __const_udelay arithmetic, single LPJ load, operands and hook/cycles call order equal base.

A49DL2 header field8 is selected_read_domain (0 before claim,1 after selected claim), tail168 within the same192-byte header and2560-byte area; all other offsets unchanged. Recorder adds no counter read, lock or IRQ-mask interval across the real read/loop. Backend claim is not proof that any physical read returned. See source-checks.json, controls.json and decoder-controls.json for the bounded checks.
''')
print(json.dumps(r,indent=2))
