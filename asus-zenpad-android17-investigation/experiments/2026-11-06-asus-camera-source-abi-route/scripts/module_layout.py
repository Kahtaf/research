from pathlib import Path
import struct,subprocess,json,os,resource
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-camera-source-abi-route')
def inspect(path,addresses):
 d=path.read_bytes();is64=d[4]==2;ptr='Q' if is64 else 'I';width=8 if is64 else 4
 if is64:phoff=struct.unpack_from('<Q',d,32)[0];ents,num=struct.unpack_from('<HH',d,54)
 else:phoff=struct.unpack_from('<I',d,28)[0];ents,num=struct.unpack_from('<HH',d,42)
 loads=[]
 for i in range(num):
  off=phoff+i*ents
  if is64:t,flags,fo,va,pa,sz,ms,al=struct.unpack_from('<IIQQQQQQ',d,off)
  else:t,fo,va,pa,sz,ms,flags,al=struct.unpack_from('<IIIIIIII',d,off)
  if t==1:loads.append((va,fo,sz))
 def read(va,n):
  for start,fo,sz in loads:
   if start<=va and va+n<=start+sz:return d[fo+va-start:fo+va-start+n]
  return b''
 print('ELF',path.name)
 for label,va,size in addresses:
  data=read(va,size);print(label,'vaddr',hex(va),'data',data.hex())
  if label=='HMI':
   print('HEADER tag,module_api,hal_api',struct.unpack_from('<IHH',data))
   for ofs in range(0xf8 if is64 else 0x80,min(size,0x168 if is64 else 0xc0),width):
    print('HMI_FIELD',hex(ofs),hex(struct.unpack_from('<'+ptr,data,ofs)[0]))
 print('RELOCS',subprocess.run(['readelf','-rW',str(path)],capture_output=True,text=True).stdout)
inspect(r/'public/lib64_hw_camera.mt8163.so',[('force-property',0x9cd9,28),('platform-library',0xa923,45)])
inspect(r/'public/lib64_libcam.device3.so',[('hw-device-template',0x10b30,120),('camera3-ops-template',0x10ba8,128)])
inspect(r/'public/lib64_libcam_platform.so',[('platform-vtable',0x2c70,48)])
print('ABI_PROBE_RODATA',subprocess.run(['readelf','-x','.rodata',str(r/'abi-out/libp00a_camera_abi_probe.so')],capture_output=True,text=True).stdout)
