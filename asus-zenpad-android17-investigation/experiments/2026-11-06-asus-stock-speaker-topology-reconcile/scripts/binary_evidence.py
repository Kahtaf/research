"""Decode public FDT + embedded kallsyms; disassemble unchanged image bytes in an ELF container."""
import hashlib,json,re,struct,sys,resource
from pathlib import Path
from bounded import ROOT,run
resource.setrlimit(resource.RLIMIT_CPU,(45,45))
try:resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
except (ValueError,OSError):pass
H=lambda x:hashlib.sha256(x).hexdigest()
def fdt(data):
 magic,size,so,st,_,_,_,_,ss,sz=struct.unpack_from('>10I',data);assert magic==0xd00dfeed and size==len(data)
 strings=data[st:st+ss]; off=so;stack=[];nodes={}
 while off<so+sz:
  tag=struct.unpack_from('>I',data,off)[0];off+=4
  if tag==1:
   end=data.index(0,off);stack.append(data[off:end].decode());off=(end+4)&~3;nodes['/'.join(stack) or '/']={}
  elif tag==2:stack.pop()
  elif tag==3:
   n,no=struct.unpack_from('>II',data,off);off+=8;name=strings[no:strings.index(0,no)].decode();nodes['/'.join(stack) or '/'][name]=data[off:off+n];off=(off+n+3)&~3
  elif tag==9:break
  else:assert tag==4
 return nodes
def dt_receipt(data):
 nodes=fdt(data); out={}
 for p,props in nodes.items():
  if any(s in p for s in ['audexamp','usb-dpn','11220000','11291000']) or any(b'switch-mode-delay'==k.encode() for k in props) or 'usb_dpn_sel-gpio' in props:
   out[p]={k:({'strings':v.rstrip(b'\0').decode().split('\0')} if v and v[-1:]==b'\0' and all(32<=b<127 or b==0 for b in v) else {'hex':v.hex(),'u32be':list(struct.unpack('>'+str(len(v)//4)+'I',v)) if len(v)%4==0 else None}) for k,v in props.items()}
 return {'selected_nodes':out,'switch_mode_delay_nodes':[p for p,v in nodes.items() if 'switch-mode-delay' in v],'gpio24_nodes':{p:{k:v.hex() for k,v in props.items()} for p,props in nodes.items() if any(k in ('pins','pinmux') and v==bytes.fromhex('00001800') for k,v in props.items())},'headset_amp_switch_nodes':[p for p,v in nodes.items() if 'mediatek,headset-amp-switch' in v]}
def tokens(data):
 for m in re.finditer(rb'\x00\x00[\x01-\x40]\x00[\x02-\x80]\x00',data):
  i=m.start()
  if i%2 or i+512>len(data):continue
  idx=struct.unpack_from('<256H',data,i)
  if not all(a<b for a,b in zip(idx,idx[1:])) or idx[-1]>8192:continue
  for tail in range(1,64):
   for pad in range(256):
    start=i-pad-idx[-1]-tail
    if start%256:continue
    table=data[start:i-pad]; ts=table.split(b'\0')
    if len(ts)!=257 or ts[-1]!=b'' or any(any(c<32 or c>126 for c in t) for t in ts[:-1]):continue
    offsets=[];n=0
    for t in ts[:-1]:offsets.append(n);n+=len(t)+1
    if offsets==list(idx) and sum(bool(t) for t in ts[:-1])>128:return start,i,ts[:-1]
 raise RuntimeError('No validated kallsyms token table')
def symbols(data):
 table,idx,ts=tokens(data)
 candidates=[]
 for co in range(256,table,256):
  n=struct.unpack_from('<Q',data,co)[0]
  if not 10000<n<300000:continue
  for mode in ['absolute','relative']:
   addrstart=co-((n*8+255)&~255) if mode=='absolute' else co-256-((n*4+255)&~255)
   if addrstart<0:continue
   candidates.append((co,n,addrstart,mode))
 for co,n,addrstart,mode in candidates:
  if struct.unpack_from('<Q',data,co)[0]!=n:continue
  namestart=co+256;pos=namestart; names=[];markers=[]
  try:
   for j in range(n):
    if j%256==0:markers.append(pos-namestart)
    length=data[pos];pos+=1;assert length>0
    name=b''.join(ts[c] for c in data[pos:pos+length]).decode();pos+=length;assert len(name)>1
    names.append(name)
   markpos=(pos+255)&~255;got=struct.unpack_from('<'+str(len(markers))+'Q',data,markpos)
   assert list(got)==markers;assert ((markpos+8*len(markers)+255)&~255)==table
  except (AssertionError,IndexError,UnicodeDecodeError,struct.error):continue
  if mode=='absolute':
   addrs=struct.unpack_from('<'+str(n)+'Q',data,addrstart)
   if addrs[0]>>48!=0xffff or not all(a<=b for a,b in zip(addrs,addrs[1:])):continue
  else:
   base=struct.unpack_from('<Q',data,co-256)[0];offsets=struct.unpack_from('<'+str(n)+'I',data,addrstart);addrs=[base+x for x in offsets]
   assert all(a<=b for a,b in zip(addrs,addrs[1:])), 'absolute-percpu relative encoding unsupported'
  return {'count':n,'mode':mode,'addresses_offset':addrstart,'count_offset':co,'names_offset':namestart,'markers_offset':markpos,'token_table_offset':table,'token_index_offset':idx},list(zip(addrs,names))
 raise RuntimeError('No validated kallsyms names/markers/address structure')
def elf(raw,base,syms):
 # ELF64 AArch64 ET_EXEC. Unchanged file bytes at .text; generated symbol metadata only.
 shstr=b'\0.text\0.symtab\0.strtab\0.shstrtab\0';strings=b'\0';stab=bytes(24)
 for addr,name in syms:
  no=len(strings);strings+=name[1:].encode()+b'\0';stab+=struct.pack('<IBBHQQ',no,0x12,0,1,addr,0)
 off=64;textoff=off;off+=len(raw);off=(off+7)&~7;stabo=off;off+=len(stab);stro=off;off+=len(strings);shstro=off;off+=len(shstr);sho=(off+7)&~7
 hdr=b'\x7fELF\x02\x01\x01'+bytes(9)+struct.pack('<HHIQQQIHHHHHH',2,183,1,base,0,sho,0,64,0,0,64,5,4)
 body=bytearray(hdr);body+=raw;body+=bytes(stabo-len(body));body+=stab+strings+shstr;body+=bytes(sho-len(body));body+=bytes(64)
 for vals in [(1,1,6,base,textoff,len(raw),0,0,4,0),(7,2,0,0,stabo,len(stab),3,1,8,24),(15,3,0,0,stro,len(strings),0,0,1,0),(23,3,0,0,shstro,len(shstr),0,0,1,0)]:body+=struct.pack('<IIQQQQIIQQ',*vals)
 return body
def main():
 for label,dt in [('stock-public','appended.dtb'),('bmc','asus-p00a.dtb')]:
  raw=(ROOT/'inputs'/label/'Image').read_bytes();meta,syms=symbols(raw)
  lookup={name[1:]:addr for addr,name in syms};base=(lookup['_stext'] & ~0xfffff) + 0x80000;assert lookup['_stext']-base==0x1000
  meta.update({'Image_sha256':H(raw),'image_base':hex(base),'embedded_config_found':b'IKCFG_ST' in raw,'linux_version':re.search(rb'Linux version [^\0]+',raw).group().decode(errors='replace')})
  (ROOT/f'evidence/{label}-kallsyms.json').write_text(json.dumps(meta,indent=2)+'\n')
  (ROOT/f'evidence/{label}-symbols.tsv').write_text(''.join(f'{addr:016x}\t{name}\n' for addr,name in syms))
  obj=ROOT/f'evidence/{label}-actual-bytes.elf';obj.write_bytes(elf(raw,base,syms))
  chosen=[(addr,name) for addr,name in syms if name[1:] in ['Ext_Speaker_Amp_Change','Ext_Speaker_Amp_Set','Speaker_Amp_Change','Speaker_Amp_Set','Speaker_ClassAB_Open','Speaker_ClassAB_close','mtk_mt6323_codec_init','mt_soc_get_dts_config','AudDrv_GPIO_EXTAMP_Select','AudDrv_GPIO_EXTAMP_Set','setUsingExtSpeaker','SetDLSrc2']]
  (ROOT/f'evidence/{label}-selected-symbols.json').write_text(json.dumps({name[1:]:hex(addr) for addr,name in chosen},indent=2)+'\n')
  chunks=[]
  for addr,name in chosen:
   greater=[a for a,n in syms if a>addr];end=min(greater) if greater else addr+4
   assert 0<=addr-base<end-base<=len(raw),(name,hex(addr),hex(base))
   chunks.append(run(['/Library/Developer/CommandLineTools/usr/bin/llvm-objdump','-d','--no-show-raw-insn',f'--start-address={addr}',f'--stop-address={end}',obj]).decode())
  (ROOT/f'evidence/{label}-disassembly.txt').write_text('\n'.join(chunks))
  (ROOT/f'evidence/{label}-dt.json').write_text(json.dumps(dt_receipt((ROOT/'inputs'/label/dt).read_bytes()),indent=2)+'\n')
  print(label,meta['count'],meta['mode'],meta['image_base'],'selected',len(chosen))

if __name__=='__main__':main()
