from pathlib import Path
import json,subprocess,hashlib,struct,re,shlex
r=Path('/srv/android/asus-camera-property-map-20261106');llvm=Path('/srv/android/lineage24/prebuilts/clang/host/linux-x86/clang-r584948b/bin')
pins=json.loads((r/'input-pins.json').read_text());extra={}
for c in json.loads((r/'abi-supplement-commands.json').read_text()):
 a=c['argv']
 if '-c' not in a:continue
 flags=a[1:a.index('-Xclang')]
 p=subprocess.run([a[0],*flags,'-M',str(r/'donor/libutils/PropertyMap.cpp')],capture_output=True,text=True,check=True,timeout=30)
 for n in shlex.split(p.stdout.replace('\\\n',' ').split(':',1)[1]):
  f=Path(n);d=f.read_bytes();extra[n]={'sha256':hashlib.sha256(d).hexdigest(),'bytes':len(d)}
(r/'supplement-input-pins.json').write_text(json.dumps(extra,indent=2))
post={};changes=[]
for n,pin in pins.items():
 f=Path(n);d=f.read_bytes();got=hashlib.sha256(d).hexdigest();post[n]={'sha256':got,'bytes':len(d)}
 if got!=pin['sha256']:changes.append(n)
assert not changes
(r/'input-pins-post.json').write_text(json.dumps(post,indent=2))
old=Path('/srv/android/asus-camera-arm32-route/public/lib_libutils.so');d=old.read_bytes();off=struct.unpack_from('<I',d,32)[0];esize,num,strings=struct.unpack_from('<HHH',d,46);sh=[struct.unpack_from('<IIIIIIIIII',d,off+i*esize) for i in range(num)]
syms=subprocess.run([str(llvm/'llvm-readelf'),'--dyn-syms','-W',str(old)],capture_output=True,text=True,check=True,timeout=15).stdout
symbol_names={}
for l in syms.splitlines():
 m=re.match(r'\s*\d+:\s+([0-9a-f]+)\s+\d+\s+\w+\s+\w+\s+\w+\s+\w+\s+(\S+)',l)
 if m and int(m[1],16):symbol_names.setdefault(int(m[1],16),[]).append(m[2])
addr=0x18870
s=next(x for x in sh if x[3]<=addr and addr+44<=x[3]+x[5]);values=struct.unpack_from('<11I',d,s[4]+addr-s[3])
vtable={'source':str(old),'sha256':hashlib.sha256(d).hexdigest(),'address':hex(addr),'bytes':44,'entries':[{'slot':i,'value':hex(v),'symbol':symbol_names.get(v,[])} for i,v in enumerate(values)]}
vtable['deleting_destructor_disassembly']=subprocess.run([str(llvm/'llvm-objdump'),'-d','--demangle','--triple=thumbv7-linux-android','--start-address=0xbc10','--stop-address=0xbc38',str(old)],capture_output=True,text=True,check=True,timeout=15).stdout
(r/'oem-vtable.json').write_text(json.dumps(vtable,indent=2));print(json.dumps(vtable,indent=2))
print('PASS',len(pins),'selected frozen/own compiler inputs unchanged;',len(extra),'donor transitive pins; scratch',sum(p.stat().st_size for p in r.rglob('*') if p.is_file()))
