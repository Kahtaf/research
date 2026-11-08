"""Decode exact stock kernel kallsyms; save only selected small function slices as ELF.

No complete kernel copy is emitted. Addresses/count are discovered and cross-validated.
"""
import pathlib,struct,zlib,json,hashlib,resource,re
resource.setrlimit(resource.RLIMIT_CPU,(45,45))
R=pathlib.Path(__file__).resolve().parents[1];W=R.parent
src=W/'2026-11-06-asus-stock-only-ram-rescue-build/artifacts/base-kernel'
k=src.read_bytes();assert hashlib.sha256(k).hexdigest()=='b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880'
b=zlib.decompress(k[512:],31);align=lambda n,a=256:(n+a-1)//a*a
# Stock 3.18 absolute-address kallsyms; find the long contiguous canonical address table.
runs=[];start=None
for i in range(0,len(b)-7,8):
 v=struct.unpack_from('<Q',b,i)[0]
 if v>>32==0xffffffc0:
  if start is None:start=i
 else:
  if start is not None and i-start>400000:runs.append((start,i))
  start=None
assert len(runs)==1,runs
a,e=runs[0];n=(e-a)//8;numoff=align(e);assert struct.unpack_from('<Q',b,numoff)[0]==n
addresses=struct.unpack_from('<'+'Q'*n,b,a);assert list(addresses)==sorted(addresses)
namesoff=align(numoff+8);p=namesoff;encoded=[];markers=[]
for i in range(n):
 if i%256==0:markers.append(p-namesoff)
 size=b[p];assert 0<size<128
 encoded.append(b[p+1:p+1+size]);p+=size+1
markeroff=align(p);stored=struct.unpack_from('<'+'Q'*len(markers),b,markeroff);assert list(stored)==markers
tokoff=align(markeroff+8*len(markers));tokens=[];idx=[];p=tokoff
for _ in range(256):
 idx.append(p-tokoff);end=b.index(b'\0',p);tokens.append(b[p:end].decode('ascii'));p=end+1
indexoff=align(p);assert list(struct.unpack_from('<256H',b,indexoff))==idx
symbols=[]
for addr,name in zip(addresses,encoded):
 text=''.join(tokens[t] for t in name);assert re.fullmatch(r'[a-zA-Z?][a-zA-Z0-9_.$@]+',text),text
 symbols.append((addr,text[0],text[1:]))
sym={name:addr for addr,t,name in symbols}
base=sym.get('_text',0xffffffc000080000)
assert base==0xffffffc000080000
selected=['unpack_to_rootfs','populate_rootfs','early_initrd','early_init_dt_check_for_initrd','early_init_dt_setup_initrd_arch','ffs_function_enable','functionfs_ready_callback','functionfs_closed_callback','android_enable','android_disable','initrd_start','initrd_end','__initramfs_start','__initramfs_size','_text','_end','kernel_init']
out={}
dest=R/'extracted/kernel-functions';dest.mkdir(exist_ok=True)
for name in selected:
 if name not in sym:continue
 addr=sym[name];off=addr-base
 greater=[v for v,t,nm in symbols if v>addr];size=min(greater)-addr if greater else 0
 out[name]=dict(address=hex(addr),image_offset=off,next_symbol_delta=size)
 if name in ('initrd_start','initrd_end','__initramfs_start','__initramfs_size','_text','_end'):continue
 assert 0<=off<len(b) and 0<size<=32768
 code=b[off:off+size];out[name]['slice_sha256']=hashlib.sha256(code).hexdigest()
 # Minimal ELF64 executable section lets the installed LLVM disassembler read a bounded slice.
 names=b'\0.text\0.shstrtab\0';dataoff=64;stroff=dataoff+len(code);shoff=(stroff+len(names)+7)//8*8
 eh=b'\x7fELF\x02\x01\x01'+bytes(9)+struct.pack('<HHIQQQIHHHHHH',1,183,1,0,0,shoff,0,64,0,0,64,3,2)
 sh=bytes(64)+struct.pack('<IIQQQQIIQQ',1,1,6,addr,dataoff,len(code),0,0,4,0)+struct.pack('<IIQQQQIIQQ',7,3,0,0,stroff,len(names),0,0,1,0)
 (dest/(name+'.elf')).write_bytes(eh+code+names+bytes(shoff-stroff-len(names))+sh)
report=dict(kernel_sha256=hashlib.sha256(k).hexdigest(),expanded_sha256=hashlib.sha256(b).hexdigest(),kallsyms=dict(addresses_offset=a,count=n,num_offset=numoff,names_offset=namesoff,markers_offset=markeroff,token_table_offset=tokoff,token_index_offset=indexoff,all_names_valid=True,all_markers_valid=True,all_token_indices_valid=True),selected_symbols=out)
(R/'evidence/kernel-contract.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
