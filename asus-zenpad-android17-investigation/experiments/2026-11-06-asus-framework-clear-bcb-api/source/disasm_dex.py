from pathlib import Path
import re,json
from dex import Dex
S=Path(__file__).resolve().parents[1]
OP={int(op,16):(name,fmt,index) for op,name,fmt,index in re.findall(r'V\((0x[0-9A-Fa-f]+),\s*\w+,\s*"([^"]+)",\s*k(\w+),\s*\w+,\s*k(\w+),',(S/'source/reference-dex_instruction_list.h').read_text())}
assert len(OP)==256

def signed(x,n):return x-(1<<n) if x>>(n-1)&1 else x

def decode(d,code):
 u=code['units'];p=0;rows=[]
 def i32(p):return signed(u[p]|u[p+1]<<16,32)
 def ref(kind,i):
  if kind=='IndexStringRef':return d.string(i)
  if kind=='IndexMethodRef':return d.method(i)
  if kind=='IndexFieldRef':return d.field(i)
  if kind=='IndexTypeRef':return d.type(i)
  return f'{kind}:{i}'
 while p<len(u):
  word=u[p];opcode=word&255;hi=word>>8;a=hi&15;b=hi>>4
  r={'pc':p,'byte_offset':code['code_offset']+16+p*2,'opcode':opcode};regs=[]
  if opcode==0 and hi:
   count=u[p+1]
   if hi==1:
    width=4+2*count;r.update(name='packed-switch-payload',keys=list(range(i32(p+2),i32(p+2)+count)),offsets=[i32(p+4+j*2) for j in range(count)])
   elif hi==2:
    width=2+4*count;r.update(name='sparse-switch-payload',keys=[i32(p+2+j*2) for j in range(count)],offsets=[i32(p+2+count*2+j*2) for j in range(count)])
   elif hi==3:count=u[p+2]|u[p+3]<<16;width=4+(u[p+1]*count+1)//2;r.update(name='array-data-payload',count=count,element_width=u[p+1])
   else:raise AssertionError(('payload',hex(word)))
  else:
   name,fmt,index=OP[opcode];width=int(fmt[0]);r.update(name=name,format=fmt)
   if fmt=='10x':pass
   elif fmt=='12x':regs=[a,b]
   elif fmt=='11x':regs=[hi]
   elif fmt=='11n':regs=[a];r['literal']=signed(b,4)
   elif fmt=='10t':r['target']=p+signed(hi,8)
   elif fmt=='20t':r['target']=p+signed(u[p+1],16)
   elif fmt=='30t':r['target']=p+i32(p+1)
   elif fmt=='22x':regs=[hi,u[p+1]]
   elif fmt=='32x':regs=[u[p+1],u[p+2]]
   elif fmt=='21s':regs=[hi];r['literal']=signed(u[p+1],16)
   elif fmt=='31i':regs=[hi];r['literal']=i32(p+1)
   elif fmt=='51l':regs=[hi];r['literal']=signed(sum(u[p+1+j]<<(16*j) for j in range(4)),64)
   elif fmt=='21h':regs=[hi];r['literal']=signed(u[p+1],16)<<(48 if 'wide' in name else 16)
   elif fmt=='21t':regs=[hi];r['target']=p+signed(u[p+1],16)
   elif fmt=='22t':regs=[a,b];r['target']=p+signed(u[p+1],16)
   elif fmt=='31t':regs=[hi];r['payload']=p+i32(p+1)
   elif fmt in ('21c','31c'):regs=[hi];idx=u[p+1]+(u[p+2]<<16 if fmt=='31c' else 0);r.update(index=idx,ref=ref(index,idx))
   elif fmt in ('22c','22cs'):regs=[a,b];idx=u[p+1];r.update(index=idx,ref=ref(index,idx))
   elif fmt=='23x':regs=[hi,u[p+1]&255,u[p+1]>>8]
   elif fmt=='22b':regs=[hi,u[p+1]&255];r['literal']=signed(u[p+1]>>8,8)
   elif fmt=='22s':regs=[a,b];r['literal']=signed(u[p+1],16)
   elif fmt in ('35c','35ms','35mi'):
    regs=([u[p+2]>>(4*j)&15 for j in range(4)]+[a])[:b];idx=u[p+1];r.update(index=idx,ref=ref(index,idx))
   elif fmt in ('3rc','3rms','3rmi'):regs=list(range(u[p+2],u[p+2]+hi));idx=u[p+1];r.update(index=idx,ref=ref(index,idx))
   else:raise AssertionError((fmt,hex(opcode)))
  r.update(width=width,raw=' '.join(f'{w:04x}' for w in u[p:p+width]),registers=regs);rows.append(r);p+=width
 assert p==len(u)
 by={r['pc']:r for r in rows}
 for r in rows:
  if 'target'in r:assert r['target'] in by
  if 'payload'in r:
   payload=by[r['payload']]
   if 'offsets'in payload:r['switch']={str(key):r['pc']+off for key,off in zip(payload['keys'],payload['offsets'])};assert all(t in by for t in r['switch'].values())
 return rows

def listing(method,code,rows):
 lines=[method,f"code_off={code['code_offset']:#x} registers={code['registers']} ins={code['ins']} outs={code['outs']} units={code['insns_size']}"]
 for r in rows:
  detail=', '.join('v'+str(n) for n in r['registers'])
  for key in ['literal','ref','target','payload','switch','keys','offsets']:
   if key in r:detail+=f' {key}={r[key]!r}'
  lines.append(f"{r['pc']:04x} @{r['byte_offset']:08x} {r['raw']:25s} {r['name']:28s} {detail}")
 lines.append('try_items='+json.dumps(code['try_items']));return '\n'.join(lines)+'\n'

def main():
 targets={
 'Landroid/os/IRecoverySystem$Stub;':None,
 'Landroid/os/IRecoverySystem$Stub$Proxy;':['clearBcb','getInterfaceDescriptor'],
 'Lcom/android/server/RecoverySystemService;':None,
 'Lcom/android/server/RecoverySystemService$BinderService;':['clearBcb','setupOrClearBcb','connectService'],
 'Landroid/app/ContextImpl;':['enforceCallingOrSelfPermission','checkCallingOrSelfPermission','checkPermission','enforce'],
 'Landroid/app/ActivityManager;':['checkComponentPermission'],
 'Landroid/os/UserHandle;':['getAppId'],
 'Lcom/android/server/am/ActivityManagerService;':['checkPermission','checkComponentPermission'],
 }
 out=[]
 for path in sorted((S/'inputs').glob('*.dex*')):
  d=Dex(path)
  for cl,names in targets.items():
   if cl not in d.classes:continue
   data=d.classdata(cl)
   for m in data['methods']:
    name=m['name'].split('->')[1].split('(')[0]
    if not m['code_offset'] or (names is not None and name not in names):continue
    code=d.code(m['code_offset']);rows=decode(d,code);item=dict(file=str(path.relative_to(S)),method=m['name'],method_index=m['index'],class_info={k:v for k,v in data.items() if k!='methods'},code={k:v for k,v in code.items() if k!='units'},instructions=rows);out.append(item)
    dst=cl.split('/')[-1][:-1]+'--'+name+('-with-token' if 'IILandroid/os/IBinder;' in m['name'] else '')
    (S/'evidence'/(dst+'.txt')).write_text(listing(m['name'],code,rows))
 (S/'evidence/decoded-methods.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'decoded_methods':len(out)}))
if __name__=='__main__':main()
