from pathlib import Path
import hashlib,io,json,zipfile,gzip,subprocess as s,shutil,re,os
R=Path('/srv/android/asus-android17-runtime-prereqs'); I=R/'inputs'; T=Path('/srv/android/lineage24')
manifest=[]
def digest(b): return hashlib.sha256(b).hexdigest()
def freeze(src,dst,expected=None):
 src=Path(src); a=src.stat(); data=src.read_bytes(); b=src.stat(); assert (a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_ino,b.st_size,b.st_mtime_ns)
 assert digest(src.read_bytes())==digest(data)
 if expected: assert digest(data)==expected
 dst=I/dst; dst.parent.mkdir(parents=True,exist_ok=True); assert not dst.exists(); dst.write_bytes(data)
 manifest.append(dict(source=str(src),path=str(dst.relative_to(I)),sha256=digest(data),bytes=len(data)))
 return data
cap=freeze('/srv/android/asus-device-product/result/com.android.adbd.capex','adbd.capex','ef9ffc28b94dc18e520f503d46ff099e7ef2e9fa366906b6d54bc2e7da6eea47')
google=Path('/srv/android/asus-device-product/google-inline/MindTheGapps-17.0.0-arm64-20261022_132445.zip')
assert digest(google.read_bytes())=='a6844eeb2613541558237e467b20feb01f8b45b2ebab0109834140ea59b6ca4d'
with zipfile.ZipFile(google) as z:
 names=[n for n in z.namelist() if n.endswith('.apex')]; print(names)
 assert len(names)==1
 g=z.read(names[0]); (I/'google.apex').write_bytes(g)
 manifest.append(dict(source=str(google)+'!'+names[0],path='google.apex',sha256=digest(g),bytes=len(g)))
for name,data in [('adbd',cap),('google',g)]:
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  if 'original_apex' in z.namelist():
   data=z.read('original_apex'); (I/(name+'.apex')).write_bytes(data)
   z=zipfile.ZipFile(io.BytesIO(data))
  image=z.read('apex_payload.img'); (I/(name+'.img')).write_bytes(image)
  manifest.append(dict(source=name+'.apex!apex_payload.img',path=name+'.img',sha256=digest(image),bytes=len(image)))
# Preserve the successful actual SDK37 startup binary inputs from its immutable CPIO.
a=gzip.decompress(Path('/srv/android/asus-userspace-startup/checkpoint/run-r2-advice/initramfs.cpio.gz').read_bytes()); pos=0
while pos<len(a):
 assert a[pos:pos+6]==b'070701'
 vals=[int(a[pos+6+i*8:pos+14+i*8],16) for i in range(13)]; size=vals[6]; n=vals[11]
 name=a[pos+110:pos+110+n-1].decode(); pos=(pos+110+n+3)&~3
 data=a[pos:pos+size]; pos=(pos+size+3)&~3
 if name=='TRAILER!!!': break
 if name.startswith('system/') and size:
  dst=I/'root'/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
  manifest.append(dict(source='startup-checkpoint/initramfs:'+name,path=str(dst.relative_to(I)),sha256=digest(data),bytes=len(data)))
# Freeze real core libraries from preserved Soong intermediates, with double-read hash checking.
base=T/'out/soong/.intermediates'; names={}
for p in base.rglob('*.so'):
 if p.parent.name in ('android_arm64_armv8-a_shared','android_arm64_armv8-a_shared_cfi'):
  names.setdefault(p.name,[]).append(p)
queue=['libbinder.so']; seen=set()
while queue:
 name=queue.pop()
 if name in seen or name=='ld-android.so': continue
 seen.add(name)
 dest=I/'root/system/lib64'/name
 if dest.exists(): data=dest.read_bytes()
 else:
  candidates=names.get(name,[]); assert len(candidates)==1,(name,candidates)
  data=freeze(candidates[0],'root/system/lib64/'+name)
 dyn=s.check_output(['readelf','-d',str(dest)],text=True)
 queue+=re.findall(r'Shared library: \[(.*?)\]',dyn)
# Header inputs from immutable Git commits, never a source worktree copy.
headers=[('bionic',['libc/include','libc/kernel/uapi','libc/kernel/android/uapi']),('frameworks/native',['libs/binder/include','libs/binder/ndk/include_cpp','libs/binder/ProcessState.cpp','libs/binder/IPCThreadState.cpp','libs/binder/Android.bp']),('system/core',['libutils/include','libutils/binder/include','libcutils/include','libsystem/include']),('system/logging',['liblog/include']),('system/libbase',['include']),('external/libcxx',['include']),('external/libcxxabi',['include'])]
for repo,paths in headers:
 rev=s.check_output(['git','-C',str(T/repo),'rev-parse','HEAD'],text=True).strip()
 dest=I/'headers'/repo;dest.mkdir(parents=True,exist_ok=True)
 p=s.Popen(['git','-C',str(T/repo),'archive',rev,'--']+paths,stdout=s.PIPE)
 s.run(['tar','xf','-','-C',str(dest)],stdin=p.stdout,check=True);assert p.wait()==0
 manifest.append(dict(source=repo,commit=rev,paths=paths))
for n in ['crtbegin_dynamic','crtend_android']:
 freeze(base/f'bionic/libc/{n}/android_arm64_armv8-a/{n}.o',n+'.o')
(R/'evidence/input-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('frozen libraries',sorted(seen))
