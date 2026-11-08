from pathlib import Path
import subprocess,re,json,hashlib,struct
r=Path('/srv/android/asus-camera-property-map-20261106')
llvm=Path('/srv/android/lineage24/prebuilts/clang/host/linux-x86/clang-r584948b/bin')
src=Path('/srv/android/asus-camera-arm32-route/public/vendor_lib_libcam_utils.so')
assert hashlib.sha256(src.read_bytes()).hexdigest()=='be8cb386e5f5ea7045b24017870d85b67774518f6e9ae9efd3ed1c00f5dcdcec'
commands=[]
def run(a):
 p=subprocess.run(list(map(str,a)),capture_output=True,text=True,timeout=30);commands.append({'argv':list(map(str,a)),'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,p.stderr;return p.stdout
old=run([llvm/'llvm-readelf','--dyn-syms','-d','-W',src])
imports=re.findall(r'UND\s+(\S*PropertyMap\S*)',old);assert len(imports)==9 and len(set(imports))==9
mapping={n:n.replace('11PropertyMap','11AsusPropMap') for n in imports}
assert all(len(a)==len(b) and a!=b for a,b in mapping.items())
mapfile=r/'src/import-renames.txt';mapfile.write_text(''.join(a+' '+b+'\n' for a,b in mapping.items()))
dst=r/'arm/libcam_utils.property-map-WITNESS.so'
run(['patchelf','--output',dst,'--rename-dynamic-symbols',mapfile,'--add-needed','libasus_camera_legacy_property_map.so',src])
new=run([llvm/'llvm-readelf','--dyn-syms','-d','-W',dst]);(r/'arm/importer-elf.txt').write_text(new)
def symbols(s):
 out=[]
 for l in s.splitlines():
  m=re.match(r'\s*\d+:\s+\w+\s+(\d+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\S+)',l)
  if m:
   size,typ,bind,vis,index,name=m.groups();out.append((mapping.get(name,name),size,typ,bind,vis,index=='UND'))
 return sorted(out)
assert symbols(old)==symbols(new)
needed=lambda s:re.findall(r'Shared library: \[(.*?)\]',s)
assert sorted(needed(new))==sorted(needed(old)+['libasus_camera_legacy_property_map.so'])
assert not re.findall(r'UND\s+(\S*PropertyMap\S*)',new)
assert set(re.findall(r'UND\s+(\S*AsusPropMap\S*)',new))==set(mapping.values())
def sections(data):
 bits=data[4];assert data[5]==1
 if bits==1: off=struct.unpack_from('<I',data,32)[0];esize,num,strings=struct.unpack_from('<HHH',data,46);fmt='<IIIIIIIIII'
 else:off=struct.unpack_from('<Q',data,40)[0];esize,num,strings=struct.unpack_from('<HHH',data,58);fmt='<IIQQQQIIQQ'
 sh=[struct.unpack_from(fmt,data,off+i*esize) for i in range(num)];st=sh[strings];names=data[st[4]:st[4]+st[5]];out={}
 for h in sh:
  n=names[h[0]:].split(b'\0')[0].decode();out[n]=(h,data[h[4]:h[4]+h[5]])
 return out
before=sections(src.read_bytes());after=sections(dst.read_bytes());preserved={}
for n in ['.text','.rodata','.data']:
 if n in before: assert before[n][1]==after[n][1];preserved[n]=hashlib.sha256(before[n][1]).hexdigest()
exports=run([llvm/'llvm-readelf','--dyn-syms','-W',r/'arm/libasus_camera_legacy_property_map.so'])
assert all(n in exports for n in mapping.values())
assert not re.search(r'\s_ZN[K]?7android11PropertyMap',exports)
receipt={'status':'offline ELF binding witness only; not a loaded or integrated camera library','source':str(src),'pre_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'post_original_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'staged':str(dst),'staged_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'mapping':mapping,'preserved_sections':preserved,'patchelf_sha256':hashlib.sha256(Path('/usr/bin/patchelf').read_bytes()).hexdigest(),'commands':commands}
(r/'binding.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({k:v for k,v in receipt.items() if k!='commands'},indent=2))
