from pathlib import Path
import json,hashlib,base64
r=Path('/srv/android/asus-camera-property-map-review-20261106');assert r.is_dir()
f=Path('/srv/android/asus-camera-arm32-route/cpp-out/sdk37')
print(json.dumps({'cpu':list(os.sched_getaffinity(0)),'address_space':resource.getrlimit(resource.RLIMIT_AS),'cpu_seconds':resource.getrlimit(resource.RLIMIT_CPU)}))
original=Path('/srv/android/asus-camera-arm32-route/public/vendor_lib_libcam_utils.so').read_bytes()
assert hashlib.sha256(original).hexdigest()=='be8cb386e5f5ea7045b24017870d85b67774518f6e9ae9efd3ed1c00f5dcdcec'
(r/'importer-original.so').write_bytes(original)
print('IMPORTER verified',len(original))
# Copy only the frozen String16 header and its declared transitive header closure, never active source.
q=[f/'system/core/libutils/include/utils/String16.h'];done=set()
import re
while q:
 p=q.pop()
 if p in done:continue
 done.add(p);data=p.read_bytes();dest=r/'include/utils'/p.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 print('HEADER',p,len(data),hashlib.sha256(data).hexdigest())
 for inc in re.findall(rb'#include\s+[<"](utils/[^>"]+)[>"]',data):
  n=inc.decode()
  for root in [f/'system/core/libutils/include',f/'system/core/libutils/binder/include']:
   candidate=root/n
   if candidate.is_file():q.append(candidate);break
print('SCRATCH_BYTES',sum(p.stat().st_size for p in r.rglob('*') if p.is_file()))
