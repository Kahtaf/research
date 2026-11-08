from pathlib import Path
import os,resource,subprocess,struct,json,hashlib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-camera-arm32-route');out=[]
def data_at(d,va,n):
 phoff=struct.unpack_from('<I',d,28)[0];ents,num=struct.unpack_from('<HH',d,42)
 for i in range(num):
  t,fo,v,pa,sz,ms,flags,al=struct.unpack_from('<IIIIIIII',d,phoff+i*ents)
  if t==1 and v<=va and va+n<=v+sz:return d[fo+va-v:fo+va-v+n]
 raise ValueError(hex(va))
def literal(d,pool,pc):
 v=struct.unpack('<I',data_at(d,pool,4))[0]+pc
 return {'pool':hex(pool),'pc':hex(pc),'target':hex(v),'string':data_at(d,v,120).split(b'\0')[0].decode(errors='replace')}
for n in ['vendor_lib_libcam.device3.so','vendor_lib_libcam_platform.so','vendor_lib_hw_camera.mt8163.so','vendor_lib_libcam.metadataprovider.so']:
 p=r/'public'/n;d=p.read_bytes();row={'file':n,'sha256':hashlib.sha256(d).hexdigest()}
 row['relocs']=subprocess.run(['readelf','-rW',p],capture_output=True,text=True,check=True).stdout
 if 'device3' in n:
  matches=[];start=0
  while True:
   k=d.find(struct.pack('<II',0x48574454,0x302),start)
   if k<0:break
   matches.append({'file_offset':hex(k),'device_and_following_128_bytes':d[k:k+128].hex(),'words':list(struct.unpack('<32I',d[k:k+128]))});start=k+1
  row['templates']=matches
 if 'hw_camera' in n:row['selector_literals']=[literal(d,0x4ff4,0x4e06),literal(d,0x4ff8,0x4e08)]
 if 'metadataprovider' in n:row['lookup_literals']=[literal(d,0xea10,0xe916),literal(d,0xea14,0xe918),literal(d,0xea30,0xe94c),literal(d,0xea34,0xe9be)]
 out.append(row)
print(json.dumps(out))
