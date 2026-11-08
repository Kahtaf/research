"""One small host contract check; this is not physical execution/retention proof."""
from pathlib import Path
import json,struct,sys,hashlib
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parent/'2026-11-07-asus-linux49-failure-log-package/source'))
import fdt
DT=(R/'source/expected-runtime.dtb').read_bytes();I=json.loads((R/'evidence/identity.json').read_text());TAG=I['tag'].encode()
h,n,t=fdt.parse(DT)
assert len(DT)==63745 and hashlib.sha256(DT).hexdigest()==I['expected_runtime_dtb_sha256']
assert n['']['compatible'].split(b'\0')[0]==b'asus,p00a'
assert n['']['#address-cells']==n['']['#size-cells']==bytes.fromhex('00000002')
assert n['/reserved-memory']=={'#address-cells':bytes.fromhex('00000002'),'#size-cells':bytes.fromhex('00000002'),'ranges':b''}
seen=set()
for token,path,*_ in t:
 if token==1:
  assert path not in seen;seen.add(path)
assert DT[40:h[2]]==bytes(h[2]-40), 'No extra memreserve aliases'
matches=[]
for path,props in n.items():
 if not path.startswith('/reserved-memory/') or 'reg' not in props:continue
 reg=props['reg'];assert len(reg)>0 and len(reg)%16==0
 for i in range(0,len(reg),16):
  base,size=struct.unpack_from('>QQ',reg,i)
  assert base+size<=2**64
  if size and base<0x44480000 and base+size>0x44400000:
   matches.append(path)
   assert props=={'compatible':b'mediatek,ram_console\0','reg':bytes.fromhex('00000000444000000000000000080000')}
assert matches==['/reserved-memory/ram_console-reserved-memory']
assert n['/memory@00000000']['reg']==bytes.fromhex('0000000040000000000000007d600000')
assert n['/chosen']['linux,initrd-start']==bytes.fromhex('44000000') and n['/chosen']['linux,initrd-end']==bytes.fromhex('4403f007')
assert not any(a.startswith((b'initrd=',b'mem=')) for a in n['/chosen']['bootargs'].rstrip(b'\0').split())

def admit(header,dt=DT,mmu=False,cache=False,fdt_pa=0x47000000,kernel=(0x40080000,0x41200000)):
 if mmu or cache or fdt_pa%8 or not (0x40000000<=fdt_pa<=0xbd600000-len(DT)):return None
 end=fdt_pa+len(DT)
 for a,z in [(0x44400000,0x44480000),kernel,(0x44000000,0x4403f007)]:
  if fdt_pa<z and end>a:return None
 if kernel[0]<0x44480000 and kernel[1]>0x44400000:return None
 if dt!=DT:return None
 sig,pl,lpl,psz,lk,llk,lsz=struct.unpack_from('<7I',header)
 ap=(psz+63)&~63;al=(lsz+63)&~63
 if sig!=0x43474244 or (psz and pl<64) or pl+ap!=lpl:return None
 pend=lpl+ap
 if pend>0x80000 or (lsz and (lk<64 or lk<pend)) or lk+al!=llk:return None
 lend=llk+al;lo=lend if lsz else 512;co=lo+0x400
 if lend>0x80000 or lo<512 or pend>lo or lend>lo or co>=0x80000 or 0x80000-co<len(TAG):return None
 return lo,co,0x80000-co

original=bytearray(b'P'*0x80000)
struct.pack_into('<7I',original,0,0x43474244,64,192,128,320,576,256)
# Prior Linux fields deliberately nonsensical: they are never used for addressing.
struct.pack_into('<6I',original,0x28,*([0xffffffff]*6))
layout=admit(original);assert layout==(832,1856,0x80000-1856)
a=bytearray(original);lo,co,sz=layout
struct.pack_into('<I',a,0x34,0);struct.pack_into('<I',a,0x38,0)
a[co:co+len(TAG)]=TAG
for off,value in [(0x28,0x80000),(0x2c,lo),(0x30,co),(0x3c,sz),(0x38,len(TAG))]:struct.pack_into('<I',a,off,value)
assert a[:0x28]==original[:0x28] and a[64:co]==original[64:co] and a[co+len(TAG):]==original[co+len(TAG):]
assert struct.unpack_from('<6I',a,0x28)==(0x80000,lo,co,0,len(TAG),sz)
assert bytes(a[co:co+len(TAG)])==TAG
cases={}
for name,kw in [('changed runtime DT',{'dt':DT[:-1]+bytes([DT[-1]^1])}),('MMU on',{'mmu':True}),('D-cache on',{'cache':True}),('FDT overlaps console',{'fdt_pa':0x44400000}),('FDT outside memory bank',{'fdt_pa':0xfffffffffffff000}),('kernel overlaps console',{'kernel':(0x40080000,0x44500000)})]:
 assert admit(original,**kw) is None;cases[name]='refused before any retained store'
for name,off,value in [('bad signature',0,0),('PL reaches header',4,0),('LK arithmetic exceeds region',24,0xffffffff),('bad LK mirror',20,575),('PL exceeds Linux area',12,0xffffffff)]:
 bad=bytearray(original);struct.pack_into('<I',bad,off,value);assert admit(bad) is None;cases[name]='refused before any retained store'
result=dict(status='ONE_FOCUSED_POSITIVE_REFUSAL_SET_PASSED',positive_layout=dict(linux_offset=lo,console_offset=co,console_size=sz,tag_bytes=len(TAG)),refusals=cases,whole_runtime_DT_equality=True,compiled_contract=dict(root='asus,p00a',reserved_memory_cells='2/2',ranges_empty=True,unique_exact_intersection=matches,no_map_reusable_status_absent=True,initrd='0x44000000..0x4403f007',memory='0x40000000..0xbd600000'),PL_LK_and_reason_area_unchanged_in_model=True,limitation='Host contract model only. Actual linked bytes and physical trial are separate; absence is UNKNOWN.')
(R/'evidence/focused-guard-check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
