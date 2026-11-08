from pathlib import Path
import struct,json,hashlib
r=Path(__file__).resolve().parents[1];s=r.parent/'2026-11-06-asus-camera-property-map'
class Elf:
 def __init__(self,p):
  self.d=p.read_bytes();d=self.d;assert d[:6]==b'\x7fELF\x01\x01'
  self.e=struct.unpack_from('<HHIIIIIHHHHHH',d,16);assert self.e[0:2]==(3,40)
  self.ph=[struct.unpack_from('<8I',d,self.e[4]+i*self.e[8]) for i in range(self.e[9])]
  self.sh=[struct.unpack_from('<10I',d,self.e[5]+i*self.e[10]) for i in range(self.e[11])]
  names=self.body(self.sh[self.e[12]])
  self.names=[self.z(names,h[0]) for h in self.sh];self.sections=dict(zip(self.names,self.sh))
  for h in self.ph:
   assert h[1]+h[4]<=len(d);assert h[4]<=h[5];assert h[7] in [0,1] or h[1]%h[7]==h[2]%h[7]
  for h in self.sh:
   if h[1]!=8:assert h[4]+h[5]<=len(d)
   if h[2]&2 and h[5] and h[1]!=8:
    matches=[p for p in self.ph if p[0]==1 and p[2]<=h[3] and h[3]+h[5]<=p[2]+p[4] and p[1]+h[3]-p[2]==h[4]]
    assert matches,(self.z(names,h[0]),'not LOAD mapped')
  self.dyn=[struct.unpack_from('<iI',self.body(self.sections['.dynamic']),i) for i in range(0,self.sections['.dynamic'][5],8)];self.dyn=self.dyn[:next(i for i,v in enumerate(self.dyn) if v[0]==0)+1];self.tags=dict(self.dyn)
  for tag,name in [(5,'.dynstr'),(6,'.dynsym'),(0x6ffffef5,'.gnu.hash'),(0x6000000f,'.rel.dyn'),(23,'.rel.plt'),(0x6ffffff0,'.gnu.version'),(0x6ffffffe,'.gnu.version_r'),(0x6ffffffc,'.gnu.version_d')]:
   if tag in self.tags:assert self.tags[tag]==self.sections[name][3],(tag,name)
  strings=self.body(self.sections['.dynstr']);self.strings=strings
  h=self.sections['.dynsym'];b=self.body(h);assert h[6]==self.names.index('.dynstr')
  self.syms=[]
  for i in range(0,len(b),16):
   x=struct.unpack_from('<IIIBBH',b,i);self.syms.append((self.z(strings,x[0]),x[1],x[2],x[3],x[4],self.names[x[5]] if 0<x[5]<len(self.names) else x[5]))
  self.needed=[self.z(strings,v) for k,v in self.dyn if k==1]
 def body(self,h):return self.d[h[4]:h[4]+h[5]]
 @staticmethod
 def z(b,i):assert i<len(b);return b[i:b.index(0,i)].decode()
 def rel(self):
  out=[]
  for name in ['.rel.plt','.rel.dyn']:
   if name in self.sections and self.sections[name][1]==9:
    b=self.body(self.sections[name]);out.extend(struct.unpack_from('<II',b,i) for i in range(0,len(b),8))
  if '.rel.dyn' in self.sections and self.sections['.rel.dyn'][1]==0x60000001:
   b=self.body(self.sections['.rel.dyn']);assert b[:4]==b'APS2';pos=4
   def sleb():
    nonlocal pos
    v=shift=0
    while True:
     c=b[pos];pos+=1;v|=(c&127)<<shift;shift+=7
     if not c&128:return v-(1<<shift) if c&64 else v
   count=sleb();offset=sleb()
   while count:
    n=sleb();flags=sleb();assert 0<n<=count and not flags&12
    delta=sleb() if flags&2 else None;info=sleb() if flags&1 else None
    for _ in range(n):
     offset+=delta if flags&2 else sleb();x=info if flags&1 else sleb();out.append((offset,x))
    count-=n
   assert not any(b[pos:])
  return out
 def hashcheck(self):
  b=self.body(self.sections['.gnu.hash']);nb,first,nw,shift=struct.unpack_from('<4I',b);bloom=struct.unpack_from('<'+'I'*nw,b,16);buckets=struct.unpack_from('<'+'I'*nb,b,16+4*nw);chains=struct.unpack_from('<'+'I'*((len(b)-16-4*nw-4*nb)//4),b,16+4*nw+4*nb)
  def gh(n):
   h=5381
   for c in n.encode():h=(h*33+c)&0xffffffff
   return h
  count=0
  for idx,sym in enumerate(self.syms[first:],first):
   name=sym[0];h=gh(name);assert bloom[(h//32)%nw] & ((1<<(h%32))|(1<<((h>>shift)%32))) == ((1<<(h%32))|(1<<((h>>shift)%32)))
   j=buckets[h%nb];found=False
   while j>=first and j<len(self.syms):
    ch=chains[j-first]
    if ch|1==h|1 and self.syms[j][0]==name:found=True;break
    if ch&1:break
    j+=1
   assert found,(name,idx);count+=1
  return count
old=Elf(r/'evidence/importer-original.so');new=Elf(s/'artifacts/arm/libcam_utils.property-map-WITNESS.so')
mapping=json.loads((s/'evidence/binding.json').read_text())['mapping']
assert all(len(a)==len(b) for a,b in mapping.items())
# Compare runtime contracts by resolved symbol identity, independently of numeric reordering.
assert len(old.syms)==len(new.syms)
byname={x[0]:x for x in new.syms}
assert len(byname)==len(new.syms)
assert sorted((mapping.get(x[0],x[0]),*x[1:5],x[5]==0) for x in old.syms)==sorted((*x[:5],x[5]==0) for x in new.syms)
section_mismatches=[{'name':x[0],'old_section':x[5],'new_section':byname[mapping.get(x[0],x[0])][5]} for x in old.syms if x[5]!=byname[mapping.get(x[0],x[0])][5]]
ra,rb=old.rel(),new.rel();assert len(ra)==len(rb)
mismatches=[];references={k:[] for k in mapping}
for (oa,ia),(ob,ib) in zip(ra,rb):
 a=old.syms[ia>>8];b=new.syms[ib>>8]
 assert oa==ob and ia&255==ib&255
 if a[0] in references:
  assert b[0]==mapping[a[0]]
  references[a[0]].append({'address':hex(oa),'type':ia&255,'old_index':ia>>8,'new_index':ib>>8})
 if mapping.get(a[0],a[0])!=b[0]:
  h=next(h for h in old.sh if h[3]<=oa< h[3]+h[5] and h[1]!=8 and h[2]&2)
  addend=struct.unpack_from('<I',old.d,h[4]+oa-h[3])[0]
  mismatches.append({'relocation_address':hex(oa),'type':ia&255,'old_index':ia>>8,'new_index':ib>>8,'old_symbol':a[0],'new_symbol':b[0],'old_value':hex(a[1]),'new_value':hex(b[1]),'addend':hex(addend)})
assert all(references.values())
for name in ['.text','.rodata','.data','.gnu.version','.gnu.version_r','.gnu.version_d','.ARM.exidx','.ARM.extab','.init_array','.fini_array','.data.rel.ro','.got','.rel.dyn']:
 if name in old.sections:assert old.body(old.sections[name])==new.body(new.sections[name]),name
assert new.needed==['libasus_camera_legacy_property_map.so']+old.needed
assert old.hashcheck()==new.hashcheck()
# Validate all original program bits remained at the same addresses, except relocated ELF metadata.
changed=[]
for name,h in old.sections.items():
 if h[2]&2 and h[1]!=8 and h[5]:
  nh=new.sections[name]
  if h[3]!=nh[3] or old.body(h)!=new.body(nh):changed.append(name)
assert set(changed)=={'.dynstr','.dynamic','.dynsym','.gnu.hash','.rel.plt','.interp','.note.android.ident','.note.gnu.build-id'},changed
out={'status':'FAIL binding preservation: packed relocations resolve different symbol identities',
 'original_sha256':hashlib.sha256(old.d).hexdigest(),'witness_sha256':hashlib.sha256(new.d).hexdigest(),
 'symbols':len(old.syms),'relocations':len(ra),'gnu_hash_lookups':new.hashcheck(),
 'needed_original_order_preserved':True,'new_needed_prepended':new.needed[0],
 'changed_allocated_sections':changed,'nine_private_import_relocation_bindings':references,
 'relocation_mismatch_count':len(mismatches),'relocation_mismatches':mismatches,
 'symbol_section_mismatch_count':len(section_mismatches),'symbol_section_mismatches':section_mismatches,
 'dlsym_imported':any(x[0]=='dlsym' for x in old.syms),'runtime_executed':False}
(r/'evidence/elf-review.json').write_text(json.dumps(out,indent=2)+'\n')
print(out['status']);print('symbols',len(old.syms),'relocations',len(ra),'wrong relocation targets',len(mismatches),'wrong symbol sections',len(section_mismatches));print(json.dumps(mismatches[:2],indent=2));print(json.dumps(section_mismatches[:2],indent=2))
assert len(mismatches)==63 and len(section_mismatches)==274
