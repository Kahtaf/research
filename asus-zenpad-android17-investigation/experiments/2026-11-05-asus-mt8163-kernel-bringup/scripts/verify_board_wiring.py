#!/usr/bin/env python3
"""Read FDT tokens and compare important compile-candidate wiring with live sysfs properties."""
import json,struct
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def fdt(path):
 b=path.read_bytes();header=struct.unpack_from('>10I',b);assert header[0]==0xd00dfeed
 off=header[2];strings=b[header[3]:header[3]+header[8]];stack=[];nodes={}
 while True:
  token=struct.unpack_from('>I',b,off)[0];off+=4
  if token==1:
   end=b.index(b'\0',off);name=b[off:end].decode();off=(end+4)&~3;stack.append(name);nodes['/'+('/'.join(stack[1:]))]={}
  elif token==2:stack.pop()
  elif token==3:
   size,nameoff=struct.unpack_from('>II',b,off);off+=8
   name=strings[nameoff:strings.index(b'\0',nameoff)].decode();nodes['/'+('/'.join(stack[1:]))][name]=b[off:off+size];off=(off+size+3)&~3
  elif token==4:pass
  elif token==9:break
  else:raise ValueError(token)
 return nodes
candidate=fdt(root/'artifacts/asus-p00a-COMPILE-ONLY.dtb')
live={}
for p in (root/'evidence/live-device-tree').rglob('*'):
 if p.is_file():
  rel=p.relative_to(root/'evidence/live-device-tree');node='/'+str(rel.parent)
  if node=='/.':node='/'
  live.setdefault(node,{})[rel.name]=p.read_bytes()
def cells(b):return list(struct.unpack('>'+str(len(b)//4)+'I',b))
def gpio(nodes,value):
 c=cells(value);target=[p for p,props in nodes.items() if props.get('phandle')==struct.pack('>I',c[0]) or props.get('linux,phandle')==struct.pack('>I',c[0])]
 assert len(target)==1,target
 return dict(controller=target[0],pin=c[1],flags=c[2])
rows=[]
for prop in ['lcm_power_gpio','lcm_reset_gpio','lcm_bl_gpio','lm_id0_gpio','lm_id1_gpio','lm_id2_gpio']:
 a=gpio(candidate,candidate['/lcm'][prop]);b=gpio(live,live['/lcm'][prop]);assert a==b,(prop,a,b);rows.append(dict(property='/lcm/'+prop,candidate=a,live=b,match=True))
for compatible in [b'goodix,gt6108\0',b'ti,bq25896\0']:
 a=[(p,v) for p,v in candidate.items() if v.get('compatible')==compatible];b=[(p,v) for p,v in live.items() if v.get('compatible')==compatible]
 assert len(a)==1 and len(b)==1
 for prop in (['reg','int-gpio','rst-gpio','power-gpio'] if compatible.startswith(b'goodix') else ['reg','pg_otg_en_soc_gpio','i2c_power_gpio']):
  av,bv=a[0][1][prop],b[0][1][prop]
  if 'gpio' in prop:av,bv=gpio(candidate,av),gpio(live,bv)
  else:av,bv=cells(av),cells(bv)
  assert av==bv,(prop,av,bv);rows.append(dict(property=a[0][0]+'/'+prop,candidate=av,live=bv,match=True))
assert candidate['/']['compatible'].startswith(b'asus,p00a\0')
(root/'evidence/board-wiring-verification.json').write_text(json.dumps(dict(status='passed',checks=len(rows),scope='Selected DT property comparison only; not electrical or runtime validation',properties=rows),indent=2)+'\n')
print('Matched',len(rows),'selected ASUS GPIO/address properties against the actual live DT.')
