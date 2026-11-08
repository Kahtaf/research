from pathlib import Path
import subprocess,json,hashlib,re,shutil
r=Path('/srv/android/asus-camera-property-map-20261106');llvm=Path('/srv/android/lineage24/prebuilts/clang/host/linux-x86/clang-r584948b/bin');cmds=[]
previous=json.loads((r/'commands.json').read_text())
def run(a):
 p=subprocess.run(list(map(str,a)),capture_output=True,text=True,timeout=40);cmds.append({'argv':list(map(str,a)),'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr});(r/'abi-supplement-commands.json').write_text(json.dumps(cmds,indent=2));assert p.returncode==0,p.stderr;return p.stdout
for arch in ['arm','arm64']:
 c=next(c for c in previous if '-c' in c['argv'] and ('/'+arch+'/legacy_property_map.o') in c['argv'][-1]);a=c['argv'];idx=a.index('-Xclang');flags=a[1:idx]
 # Unmodified old donor and all original old template/String8 headers.
 out=run([a[0],'-I'+str(r/'donor/include'),*flags,'-Xclang','-fdump-record-layouts','-Xclang','-fdump-vtable-layouts','-c',r/'donor/libutils/PropertyMap.cpp','-o',r/arch/'donor-property-map.o'])
 (r/arch/'donor-layouts.txt').write_text(out)
for arch,name in [('arm','asus-camera-arm32-route'),('arm64','asus-camera-source-abi-route')]:
 lib=Path('/srv/android')/name/'sdk37-libs/libutils.so'
 syms=run([llvm/'llvm-readelf','--dyn-syms','-W',lib]);selected=[]
 for l in syms.splitlines():
  m=re.match(r'\s*\d+:\s+([0-9a-f]+)\s+(\d+)\s+FUNC\s+\S+\s+\S+\s+\S+\s+(\S+)',l)
  if m:
   addr,size,n=m.groups()
   if any(x in n for x in ['16SortedVectorImplC2E','16SortedVectorImplD2E']):
    start=int(addr,16)&~1;selected.append(run([llvm/'llvm-objdump','-d','--demangle',*(['--triple=thumbv7-linux-android'] if arch=='arm' else []),'--start-address='+hex(start),'--stop-address='+hex(start+int(size)),lib]))
 (r/arch/'sorted-provider-ctors-dtors.txt').write_text('\n'.join(selected))
old=Path('/srv/android/asus-camera-arm32-route/public/lib_libutils.so')
syms=run([llvm/'llvm-readelf','--dyn-syms','-W',old]);rel=run([llvm/'llvm-readelf','-r','-W',old]);(r/'oem-vector-symbols-relocs.txt').write_text(syms+'\n'+rel)
print('PASS old donor compiled unchanged for both target widths; genuine sorted provider constructor/destructor and OEM vector relocation receipts saved')
