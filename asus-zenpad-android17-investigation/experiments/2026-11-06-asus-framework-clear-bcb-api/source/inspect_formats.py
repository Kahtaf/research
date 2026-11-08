from pathlib import Path
import struct,json,re,hashlib
S=Path(__file__).resolve().parents[1]
records=[]
for file in ['framework__arm64__boot-framework.oat','framework__oat__arm64__services.odex']:
 b=(S/'inputs'/file).read_bytes();base=4096;assert b[base:base+8]==b'oat\n079\0';count=struct.unpack_from('<I',b,base+20)[0];kvsize=struct.unpack_from('<I',b,base+68)[0];p=base+72+kvsize
 kv=b[base+72:p].split(b'\0');pairs={kv[i].decode():kv[i+1].decode() for i in range(0,len(kv)-1,2)}
 for index in range(count):
  n=struct.unpack_from('<I',b,p)[0];p+=4;location=b[p:p+n].decode();p+=n
  checksum,dexoff,classoff,lookup=struct.unpack_from('<4I',b,p);p+=16;start=base+dexoff
  assert b[start:start+8]==b'dex\n037\0';size=struct.unpack_from('<I',b,start+32)[0];classes=struct.unpack_from('<I',b,start+96)[0];assert base+classoff+classes*4<=len(b)
  raw=b[start:start+size];expected=(S/'inputs'/(file+f'.dex{index+1}')).read_bytes();assert raw==expected
  records.append(dict(container=file,oat_base=base,oat_version='079',record_index=index,dex_location=location,original_location_checksum=hex(checksum),embedded_header_checksum=hex(struct.unpack_from('<I',b,start+8)[0]),dex_offset_relative_oat=dexoff,dex_offset_absolute=start,classes=classes,class_offsets_relative_oat=classoff,lookup_relative_oat=lookup,compiler_filter=pairs.get('compiler-filter'),dex_sha256=hashlib.sha256(raw).hexdigest()))
(S/'evidence/oat-directory.json').write_text(json.dumps(records,indent=2)+'\n')
b=(S/'inputs/boot__file_contexts.bin').read_bytes();p=0

def take(n):
 global p
 assert n>=0 and p+n<=len(b);data=b[p:p+n];p+=n;return data

def u32():return struct.unpack('<I',take(4))[0]
def string():
 raw=take(u32());assert raw[-1:]==b'\0';return raw[:-1].decode()
assert u32()==0xf97cff8a;version=u32();assert version==4
pcre=take(u32()).decode();stems=[]
for _ in range(u32()):n=u32();raw=take(n+1);assert raw[-1]==0;stems.append(raw[:-1].decode())
rows=[]
for index in range(u32()):
 label=string();regex=string();mode,stem,meta,prefix=[u32() for _ in range(4)]
 rxsize=u32();take(rxsize);studysize=u32();take(studysize)
 rows.append(dict(index=index,context=label,regex=regex,mode=mode,stem=stem,has_meta=meta,prefix_length=prefix))
assert p==len(b),(p,len(b))
selected=[r for r in rows if any(x in r['context'] for x in ('uncrypt','misc_block_device','property_socket','binder_device','para_block','block_device'))]
(S/'evidence/file-labels.json').write_text(json.dumps(dict(format_version=version,pcre_version=pcre,stems=stems,records=len(rows),selected=selected,scope='Decoded entries only; no executing embedded PCRE bytecode and no host/device label queries'),indent=2)+'\n')
service=[line for line in (S/'inputs/boot__service_contexts').read_text().splitlines() if re.match(r'^recovery\s',line)]
props=[line for line in (S/'inputs/boot__property_contexts').read_text().splitlines() if re.match(r'^ctl\.',line)]
assert len(service)==1 and service[0].split()[1]=='u:object_r:recovery_service:s0'
matching=[line for line in props if 'ctl.clear-bcb'.startswith(line.split()[0])];matching.sort(key=lambda line:len(line.split()[0]),reverse=True)
assert matching[0].split()==['ctl.','u:object_r:ctl_default_prop:s0']
(S/'evidence/service-property-labels.json').write_text(json.dumps(dict(recovery=service[0],clear_bcb_property_match=matching[0]),indent=2)+'\n')
print(json.dumps(dict(oat_records=records,file_labels=selected),indent=2))
