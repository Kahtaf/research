from pathlib import Path
import os,stat,json,struct,io,zipfile,subprocess as s,shutil,hashlib,resource
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));E=R/'evidence';I=R/'inputs/actual';I.mkdir();raw=Path('/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw');st=raw.stat();before=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns,stat.S_IMODE(st.st_mode));assert before==(2049,27263347,3753902080,1794019280920581777,1794019538990926800,0o444)
fd=os.open(raw,os.O_RDONLY|os.O_NOFOLLOW);pread=lambda off,n:os.pread(fd,n,off);sb=pread(1024,1024);u16=lambda b,o:struct.unpack_from('<H',b,o)[0];u32=lambda b,o:struct.unpack_from('<I',b,o)[0];bs=1024<<u32(sb,24);ipg=u32(sb,40);isz=u16(sb,88);assert bs==4096 and isz==256
cache={}
def inode(n):
 if n not in cache:
  g,k=divmod(n-1,ipg);desc=pread(bs+g*32,32);cache[n]=pread(u32(desc,8)*bs+k*isz,isz)
 return cache[n]
def extents(n):
 ib=inode(n);assert u32(ib,32)&0x80000
 def walk(b,depth=0):
  assert u16(b,0)==0xf30a;d=u16(b,6);assert d<5;out=[]
  for k in range(u16(b,2)):
   logical=u32(b,12+12*k)
   if d:
    lo=u32(b,16+12*k);hi=u16(b,20+12*k);out+=walk(pread(((hi<<32)|lo)*bs,bs),depth+1)
   else:
    count=u16(b,16+12*k);hi=u16(b,18+12*k);lo=u32(b,20+12*k);assert count<32768;out.append((logical*bs,((hi<<32)|lo)*bs,count*bs))
  return out
 return walk(ib[40:100])
class File(io.RawIOBase):
 def __init__(self,n):self.n=n;self.pos=0;self.size=u32(inode(n),4)|(u32(inode(n),108)<<32);self.ex=extents(n)
 def seekable(self):return True
 def readable(self):return True
 def tell(self):return self.pos
 def seek(self,o,w=0):self.pos=o if w==0 else self.pos+o if w==1 else self.size+o;return self.pos
 def read(self,n=-1):
  if n<0:n=self.size-self.pos
  n=max(0,min(n,self.size-self.pos));out=bytearray(n)
  for l,p,z in self.ex:
   a=max(l,self.pos);b=min(l+z,self.pos+n)
   if a<b:out[a-self.pos:b-self.pos]=pread(p+a-l,b-a)
  self.pos+=n;return bytes(out)
def children(n):
 f=File(n);b=f.read();off=0;out={}
 while off<len(b):
  ino,z,nlen,t=struct.unpack_from('<IHBB',b,off);assert z>=8
  if ino:out[b[off+8:off+8+nlen].decode()]=ino
  off+=z
 return out
def lookup(path):
 n=2
 for x in path.strip('/').split('/'):n=children(n)[x]
 return n
def get(path):return File(lookup(path)).read()
def store(rel,b):p=I/rel;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(b);return dict(path=rel,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def wire(b):
 pos=0;out={}
 def vi():
  nonlocal pos
  r=0;k=0
  while True:
   v=b[pos];pos+=1;r|=(v&127)<<k
   if v<128:return r
   k+=7;assert k<70
 while pos<len(b):
  t=vi();field,kind=t>>3,t&7
  if kind==0:v=vi()
  elif kind==2:z=vi();v=b[pos:pos+z];pos+=z
  else:raise ValueError(kind)
  out.setdefault(field,[]).append(v)
 return out
D={'raw_identity_before':before,'filesystem_files':{},'packages':[]};props={}
for path in ['system/etc/linker.config.pb','system/system_ext/etc/linker.config.pb','system/product/etc/linker.config.pb','system/vendor/etc/linker.config.pb','system/etc/public.libraries.txt','system/vendor/etc/public.libraries.txt','system/etc/llndk.libraries.txt','system/etc/sanitizer.libraries.txt','system/build.prop','system/vendor/build.prop','system/system_ext/etc/build.prop','system/product/etc/build.prop']:
 try:
  b=get(path);D['filesystem_files'][path]=store(path,b)
  if path.endswith('.prop'):
   for row in b.decode().splitlines():
    if row and not row.startswith('#') and '=' in row:k,v=row.split('=',1);props[k]=v
 except KeyError:D['filesystem_files'][path]={'exists':False}
D['system_bin_linkerconfig_exists']='linkerconfig' in children(lookup('system/bin'))
init=get('system/bin/init');import re
D['actual_init_sha256']=hashlib.sha256(init).hexdigest();D['actual_init_linkerconfig_strings']=[x.decode() for x in re.findall(rb'[ -~]{8,}',init) if b'linkerconfig' in x]
fsck=R/'inputs/host-deps/root/usr/bin/fsck.erofs';tmp=R/'tmp/apex-scan';tmp.mkdir();public={r.split()[0] for r in get('system/etc/public.libraries.txt').decode().splitlines() if r and not r.startswith('#')}
for partition,directory in [('SYSTEM','system/apex'),('SYSTEM_EXT','system/system_ext/apex'),('PRODUCT','system/product/apex'),('VENDOR','system/vendor/apex')]:
 try:entries=children(lookup(directory))
 except KeyError:continue
 for name,n in sorted(entries.items()):
  if not name.endswith(('.apex','.capex')):continue
  f=File(n);outer=zipfile.ZipFile(f);manifest=outer.read('apex_manifest.pb');v=wire(manifest);apexname=v[1][0].decode();pkg=I/'apex'/apexname;pkg.mkdir(exist_ok=False,parents=True);(pkg/'outer_manifest.pb').write_bytes(manifest)
  if name.endswith('.capex'):
   with outer.open('original_apex') as src,(tmp/'original.apex').open('wb') as dst:shutil.copyfileobj(src,dst,1024**2)
   nested=zipfile.ZipFile(tmp/'original.apex');realmanifest=nested.read('apex_manifest.pb');nv=wire(realmanifest);assert nv[1]==v[1] and nv.get(7,[])==v.get(7,[]) and nv.get(8,[])==v.get(8,[]);z=nested
  else:z=outer;realmanifest=manifest
  (pkg/'manifest.pb').write_bytes(realmanifest)
  with z.open('apex_payload.img') as src,(tmp/'payload.img').open('wb') as dst:shutil.copyfileobj(src,dst,1024**2)
  dest=tmp/'extract';p=s.run([str(fsck),'--extract='+str(dest),'--no-preserve',str(tmp/'payload.img')],capture_output=True,text=True,timeout=25)
  (pkg/'extract-status.json').write_text(json.dumps(dict(rc=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0,(name,p.stderr)
  pb=dest/'etc/linker.config.pb';cfg=wire(pb.read_bytes()) if pb.is_file() else {}
  if pb.is_file():shutil.copyfile(pb,pkg/'linker.config.pb')
  vals=lambda tag:[x.decode() for x in v.get(tag,[])]
  row=dict(package_path=directory+'/'+name,partition=partition,name=apexname,namespace_name=apexname.replace('.','_'),path='/apex/'+apexname,manifest_sha256=hashlib.sha256(realmanifest).hexdigest(),provide_libs=vals(7),require_libs=vals(8),jni_libs=vals(9),has_shared_lib=bool(v.get(10)),bootstrap=bool(v.get(16,[0])[0] or v.get(15,[0])[0]),has_bin=(dest/'bin').is_dir(),has_lib=(dest/'lib').is_dir() or (dest/'lib64').is_dir(),permitted_paths=[x.decode() for x in cfg.get(1,[])],visible=bool(cfg.get(2,[0])[0]),public_libs=sorted(set(vals(7))&public) if partition in ['SYSTEM','SYSTEM_EXT'] else [],payload_files=['bin' if (dest/'bin').is_dir() else '', 'lib' if (dest/'lib').is_dir() else '', 'lib64' if (dest/'lib64').is_dir() else ''])
  if apexname=='com.android.runtime':
   assert hashlib.sha256(get(directory+'/'+name)).hexdigest()=='638361e8de6863d070e491914a75e5e5b3a07ee2929bb6b048fe5f3bbdab403d';b=(dest/'bin/linkerconfig').read_bytes();row['linkerconfig_elf']=store('runtime-apex-linkerconfig',b)
  D['packages'].append(row);outer.close()
  if name.endswith('.capex'):nested.close();(tmp/'original.apex').unlink()
  shutil.rmtree(dest);(tmp/'payload.img').unlink()
D['selected_properties']={k:v for k,v in props.items() if k in ['ro.treble.enabled','ro.product.first_api_level','ro.vndk.version','ro.product.vndk.version','ro.debuggable','ro.build.version.sdk']};st=raw.stat();after=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns,stat.S_IMODE(st.st_mode));assert before==after;D['raw_identity_unchanged']=True;(E/'actual-metadata.json').write_text(json.dumps(D,indent=2));print(json.dumps({'packages':len(D['packages']),'selected_properties':D['selected_properties'],'system_bin_linkerconfig_exists':D['system_bin_linkerconfig_exists'],'actual_init_linkerconfig_strings':D['actual_init_linkerconfig_strings'],'runtime_linkerconfig':next(x for x in D['packages'] if x['name']=='com.android.runtime')['linkerconfig_elf']},indent=2))
