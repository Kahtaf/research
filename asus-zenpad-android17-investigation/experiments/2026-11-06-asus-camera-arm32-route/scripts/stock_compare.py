from pathlib import Path
import subprocess,os,resource,hashlib,json,re
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-camera-arm32-route');(r/'public').mkdir(parents=True,exist_ok=True)
img='/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img';b=Path('/srv/android/lineage24');llvm=b/'prebuilts/clang/host/linux-x86/clang-r584948b/bin'
def get(path):
 old=Path('/srv/android/asus-camera-source-abi-route/public')/(path.split('/')[2]+'_'+path.split('/',3)[3].replace('/','_')) if path.startswith('/vendor/') else Path('/NONEXISTENT')
 if not old.exists() and path.startswith('/vendor/'):old=Path('/srv/android/asus-hardware-completeness-audit/public-selected')/old.name
 data=old.read_bytes() if old.exists() else subprocess.run(['debugfs','-R','cat '+path,img],capture_output=True,check=True).stdout
 assert len(data)<10*1024**2
 return data
rows=[]
for path in ['/bin/cameraserver','/etc/init/cameraserver.rc','/etc/init/mediaserver.rc']+[f'/vendor/{a}/{n}' for a in ['lib','lib64'] for n in ['hw/camera.mt8163.so','libcam_platform.so','libcam.device3.so','libcam.metadataprovider.so','libcameracustom.so']]:
 data=get(path);row={'path':path,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 if data.startswith(b'\x7fELF'):
  dest=r/'public'/path.strip('/').replace('/','_');dest.write_bytes(data)
  row['elfclass']=data[4];elf=subprocess.run(['readelf','-h','-dW','--dyn-syms',str(dest)],capture_output=True,text=True,check=True).stdout;row['elf']=elf
  row['sensor_constructors']=[l.split()[-1] for l in elf.splitlines() if ' FUNC ' in l and 'constructCust' in l and ' UND ' not in l]
  strings=[m.group().decode() for m in re.finditer(rb'[\x20-\x7e]{5,}',data)]
  row['selected_strings']=[s for s in strings if re.search(r'force_device|createCam|constructCust|OV5670|HM2051|OV2680|ov5670|hm2051|ov2680|metadataprovider|MetadataProvider|SENSOR_DRVNAME',s)]
  if path.startswith('/vendor/lib/') and not path.endswith('libcameracustom.so'):
   out=subprocess.run([str(llvm/'llvm-objdump'),'-d','--demangle','--triple=thumbv7-linux-android','-j','.text',str(dest)],capture_output=True,text=True,check=True).stdout
   dis=r/(dest.name+'.thumb.txt');dis.write_text(out);row['thumb_disassembly']=out
 else:row['text']=data.decode(errors='replace')
 rows.append(row)
print(json.dumps(rows))
