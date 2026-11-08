from pathlib import Path
import json,struct,hashlib,re
R=Path(__file__).resolve().parents[1]
def fdt(data):
 h=struct.unpack_from('>10I',data);assert h[0]==0xd00dfeed and h[1]==len(data)
 assert h[2]+h[9]<=len(data) and h[3]+h[8]<=len(data)
 strings=data[h[3]:h[3]+h[8]];pos=h[2];stack=[];nodes={}
 while True:
  tag=struct.unpack_from('>I',data,pos)[0];pos+=4
  if tag==1:
   end=data.index(0,pos);stack.append(data[pos:end].decode());pos=(end+4)&~3;n='/'.join(stack) or '/';assert n not in nodes;nodes[n]={}
  elif tag==2:stack.pop()
  elif tag==3:
   n,off=struct.unpack_from('>II',data,pos);pos+=8;name=strings[off:strings.index(0,off)].decode();nodes['/'.join(stack) or '/'][name]=data[pos:pos+n];pos=(pos+n+3)&~3
  elif tag==4:pass
  elif tag==9:break
  else:raise ValueError(tag)
 reservations=[];pos=h[4]
 while True:
  addr,n=struct.unpack_from('>QQ',data,pos);pos+=16
  if not(addr or n):break
  reservations.append([addr,n])
 return nodes,reservations
p=R/'remote/artifacts/arch/arm64/boot/dts/mediatek/asus-p00a.dtb';old=R.parent/'2026-11-06-asus-bmc156-full-kernel/artifacts/asus-p00a.dtb'
a,ar=fdt(old.read_bytes());b,br=fdt(p.read_bytes());assert ar==br
changes={}
for n in a.keys()|b.keys():
 if n not in a or n not in b:changes[n]='added' if n in b else 'removed';continue
 props={k:[a[n].get(k,b'').hex(),b[n].get(k,b'').hex()] for k in a[n].keys()|b[n].keys() if a[n].get(k)!=b[n].get(k)}
 if props:changes[n]=props
print(json.dumps(changes,indent=2))
(R/'evidence/dtb-raw-delta.json').write_text(json.dumps(changes,indent=2)+'\n')
def cells(v):assert len(v)%4==0;return list(struct.unpack('>'+str(len(v)//4)+'I',v))
def handles(nodes):
 d={}
 for n,props in nodes.items():
  for key in ['phandle','linux,phandle']:
   if key in props:
    c=cells(props[key]);assert len(c)==1 and (c[0] not in d or d[c[0]]==n);d[c[0]]=n
 return d
def norm(nodes):
 ids=handles(nodes);out={}
 for n,props in nodes.items():
  out[n]={}
  for k,v in props.items():
   if k in ['phandle','linux,phandle']:out[n][k]=n
   elif re.fullmatch(r'pinctrl-\d+',k) or k.endswith('-supply') or k=='mediatek,smi':out[n][k]=[ids[x] for x in cells(v)]
   elif k in ['clocks','resets','extspkamp-gpio']:
    c=cells(v);q=[];i=0;count={'clocks':'#clock-cells','resets':'#reset-cells','extspkamp-gpio':'#gpio-cells'}[k]
    while i<len(c):
     target=ids[c[i]];num=cells(nodes[target][count])[0];q.append([target,c[i+1:i+1+num]]);i+=1+num
    assert i==len(c);out[n][k]=q
   else:out[n][k]=v.hex()
 return out
na=norm(a);nb=norm(b);semantic={}
for n in na.keys()|nb.keys():
 if n not in na or n not in nb:semantic[n]='added' if n in nb else 'removed';continue
 q={k:[na[n].get(k),nb[n].get(k)] for k in na[n].keys()|nb[n].keys() if na[n].get(k)!=nb[n].get(k)}
 if q:semantic[n]=q
removed=['/soc/pinctrl@10005000/'+x for x in ['audexamphigh','audexamphigh/pins_cmd_dat','audexamplow','audexamplow/pins_cmd_dat']]
codec='/soc/mt_soc_codec_name@11220000';audio='/soc/mt_soc_dl1_pcm@11220000';pio='/soc/pinctrl@10005000'
assert set(semantic)==set(removed+[codec,audio]),semantic
assert all(semantic[n]=='removed' for n in removed)
assert set(semantic[codec])=={'asus,p00a-stock-speaker-gate','extspkamp-gpio'}
assert b[codec]['asus,p00a-stock-speaker-gate']==b''
assert nb[codec]['extspkamp-gpio']==[[pio,[28,0]]]
assert b[codec]['compatible']==b'mediatek,mt8163-soc-codec-63xx\0'
assert b[pio]['compatible']==b'mediatek,mt8163-pinctrl\0' and b[pio]['gpio-controller']==b'' and cells(b[pio]['#gpio-cells'])==[2]
assert set(semantic[audio])=={'pinctrl-names','pinctrl-5','pinctrl-6'}
usb=[n for n in a if 'usb' in n.lower()]
assert usb and all(na[n]==nb[n] for n in usb)
layout=[n for n in a if n.startswith('/reserved-memory') or n.startswith('/memory') or n=='/chosen']
assert all(a[n]==b[n] for n in layout)
assert not [n for n,props in b.items() if any(k in ['pins','pinmux'] and len(v)==4 and cells(v)[0]>>8==28 for k,v in props.items())]
selector=pio+'/usb-dpn-sel-pin'
assert cells(b['/soc/usb@11270000']['usb_dpn_sel-gpio'])==[cells(b[pio]['phandle'])[0],24,0]
assert not any(x in n for n in b for x in ['audexamphigh','audexamplow'])
rec=dict(dtb_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),dtb_bytes=p.stat().st_size,baseline_dtb_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),semantic_delta=semantic,all_other_nodes_properties_semantically_unchanged=True,usb_nodes_semantically_unchanged=usb,dtc_phandle_renumbering_expected=True,controller_path=pio,controller_phandle=cells(b[pio]['phandle'])[0],gate_specifier=[28,0],profile_zero_length_boolean=True,memory_reserved_memory_chosen_bytes_unchanged=layout,FDT_reservations_unchanged=ar,within_parent_1MiB_DTB_placement=p.stat().st_size<1024**2,gpio28_mux_assignment_added=False,dtb_verified_not_runtime_layout_or_electrical_proof=True)
(R/'evidence/dtb-verification.json').write_text(json.dumps(rec,indent=2)+'\n')
print('PASS exact semantic DT delta, GPIO28 phandle/profile, USB24 preserved, memory/reservations/chosen unchanged')
