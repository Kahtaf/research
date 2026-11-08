from pathlib import Path
import os,resource,subprocess,hashlib,json,re
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-camera-arm32-route');b=Path('/srv/android/lineage24');img='/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img';llvm=b/'prebuilts/clang/host/linux-x86/clang-r584948b/bin'
rows=[]
for path in ['/lib/'+n for n in ['libui.so','libinput.so','libarcsoft3DNR.so','libarcsoftFace.so','libarcsoftHDR.so','libarcsoftNightHawk.so','libarcsoftStabilizer.so','libcameraap.so']]+['/vendor/lib/'+n for n in ['libcam_utils.so','libcam.client.so','libmtk_mmutils.so']]:
 data=subprocess.run(['debugfs','-R','cat '+path,img],capture_output=True,check=True).stdout
 assert data.startswith(b'\x7fELF') and len(data)<10*1024**2
 dest=r/'public'/path.strip('/').replace('/','_');dest.write_bytes(data)
 elf=subprocess.run(['readelf','-dW','--dyn-syms',dest],capture_output=True,text=True,check=True).stdout
 row={'path':path,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'elf':elf}
 if path in ['/lib/libui.so','/lib/libinput.so'] or '/vendor/' in path:
  dis=subprocess.run([str(llvm/'llvm-objdump'),'-d','--demangle','--triple=thumbv7-linux-android','-j','.text',dest],capture_output=True,text=True,check=True).stdout
  lines=dis.splitlines();keep=set()
  if path.startswith('/lib/'):
   for i,line in enumerate(lines):
    if re.match(r'^[0-9a-f]+ <',line) and any(s in line for s in ['GraphicBuffer::GraphicBuffer','PropertyMap::PropertyMap']):
     stop=next((j for j in range(i+1,len(lines)) if re.match(r'^[0-9a-f]+ <',lines[j])),min(len(lines),i+500));keep.update(range(i,stop))
  else:
   for i,line in enumerate(lines):
    if 'GraphicBufferC1' in line or 'PropertyMapC1' in line:keep.update(range(max(0,i-30),min(len(lines),i+15)))
  row['selected_disassembly']='\n'.join(lines[i] for i in sorted(keep))
 rows.append(row)
for rel in ['frameworks/native/libs/ui/include/ui/GraphicBuffer.h','frameworks/native/libs/ui/include/ui/GraphicBufferMapper.h','frameworks/native/libs/ui/GraphicBuffer.cpp','frameworks/native/libs/input/PropertyMap.cpp','frameworks/native/libs/input/include/input/PropertyMap.h','hardware/interfaces/camera/provider/2.4/default/Android.bp','hardware/interfaces/camera/provider/2.4/default/ACCOUNT_REDACTED','hardware/interfaces/camera/provider/2.4/default/ACCOUNT_REDACTED']:
 p=b/rel;row={'source':str(p),'exists':p.exists()}
 if p.exists():row.update({'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'text':p.read_text()})
 rows.append(row)
print(json.dumps(rows))
