from pathlib import Path
import os,resource,subprocess,re,json,hashlib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-camera-source-abi-route');b=Path('/srv/android/lineage24');img='/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img'
def cmd(a):return subprocess.run(list(map(str,a)),text=True,capture_output=True,check=True,timeout=30).stdout
listing=cmd(['debugfs','-R','ls -p /vendor/lib64',img])
available={l.split('/')[5]:int(l.split('/')[6]) for l in listing.splitlines() if len(l.split('/'))>6 and l.split('/')[6].isdigit()}
def elf(p):
 d=cmd(['readelf','--dyn-syms','-dW',p]);needed=re.findall(r'Shared library: \[(.*?)\]',d);defined=set();undefined=set()
 for l in d.splitlines():
  m=re.match(r'\s+\d+:\s+\w+\s+\d+\s+.+?\s+(GLOBAL|WEAK)\s+\w+\s+(\S+)\s+(\S+)',l)
  if m:
   binding,index,name=m.groups();name=name.split('@')[0]
   if index=='UND':
    if binding=='GLOBAL':undefined.add(name)
   else:defined.add(name)
 return needed,defined,undefined
queue=['hw/camera.mt8163.so','libcam_platform.so','libcam.device1.so','libcam.device3.so'];seen={};defs={};total=0;leaves=set()
while queue:
 n=queue.pop(0)
 if n in seen:continue
 assert len(seen)<85
 p=r/'public'/('lib64_'+n.replace('/','_'))
 if p.exists():data=p.read_bytes()
 else:
  assert available.get(n,0)<9*1024**2
  data=subprocess.run(['debugfs','-R','cat /vendor/lib64/'+n,img],capture_output=True,check=True).stdout
 assert data.startswith(b'\x7fELF')
 total+=len(data);assert total<64*1024**2
 temp=r/'inspect-temp.so';temp.write_bytes(data)
 needed,d,u=elf(temp);temp.unlink();defs[n]=d
 seen[n]={'path':'/vendor/lib64/'+n,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'needed':needed,'undefined':sorted(u)}
 for child in needed:
  if child in available:queue.append(child)
  else:leaves.add(child)
# Include SDK37 real, already-built core providers, no Ninja or build graph evaluation.
projects={'libc':'bionic/libc/libc','libm':'bionic/libm/libm','libdl':'bionic/libdl/libdl','libc++':'prebuilts/clang/host/linux-x86/libc++','libbinder':'frameworks/native/libs/binder/libbinder','libui':'frameworks/native/libs/ui/libui','libgui':'frameworks/native/libs/gui/libgui','libcamera_client':'frameworks/av/camera/libcamera_client','libcamera_metadata':'system/media/camera/libcamera_metadata','liblog':'system/logging/liblog/liblog','libhardware':'hardware/libhardware/libhardware','libion':'system/memory/libion/libion','libjpeg':'external/libjpeg-turbo/libjpeg','libmedia':'frameworks/av/media/libmedia/libmedia','libexpat':'external/expat/libexpat','libz':'external/zlib/libz','libstdc++':'bionic/libc/libstdc++','libGLESv2':'frameworks/native/opengl/libs/libGLESv2','libEGL':'frameworks/native/opengl/libs/libEGL','libGLESv1_CM':'frameworks/native/opengl/libs/libGLESv1_CM'}
projects.update({'libnetutils':'system/core/libnetutils/libnetutils','libselinux':'external/selinux/libselinux/libselinux','libnativehelper':'libnativehelper/libnativehelper','libfs_mgr':'system/core/fs_mgr/libfs_mgr','libutilscallstack':'system/core/libutils/libutilscallstack'})
for n in ['libcutils','libutils','libsync']:projects[n]='system/core/'+n+'/'+n
modern={};exports=set().union(*defs.values());found={}
for leaf in sorted(leaves|{'libutilscallstack.so'}):
 mod=leaf.removesuffix('.so');base=b/'out/soong/.intermediates'/projects.get(mod,'NO_PATH')
 candidates=[base/v/leaf for v in ['android_arm64_armv8-a_shared','android_arm64_armv8-a_shared_cfi','android_vendor_arm64_armv8-a_shared']]
 p=next((x for x in candidates if x.is_file()),None)
 if p is None:
  modern[leaf]={'missing':True,'candidates':[str(x) for x in candidates]};continue
 dest=r/'sdk37-libs'/leaf;dest.parent.mkdir(exist_ok=True);data=dest.read_bytes() if dest.exists() else p.read_bytes();dest.write_bytes(data)
 needed,d,u=elf(dest);exports.update(d);found[leaf]=d
 modern[leaf]={'source':str(p),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'exports':len(d)}
for n,row in seen.items():row['unresolved_against_vendor_union_and_found_sdk37']=sorted(set(row['undefined'])-exports)
print(json.dumps({'architecture':'ARM64','method':'DT_NEEDED vendor closure plus explicitly seeded dlopen platform and device factories. Unresolved set is optimistic union, not namespace/version/C++ layout validation. Missing modern providers remain unresolved. Dynamic dlopen names outside explicit seeds not complete.','vendor_total_bytes_read':total,'vendor_libraries':seen,'modern_providers':modern},indent=2))
