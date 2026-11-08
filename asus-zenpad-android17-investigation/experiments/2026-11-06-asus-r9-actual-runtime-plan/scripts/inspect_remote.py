import os,pathlib,json,hashlib,struct,zlib,stat,resource,signal,subprocess
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(90)
P=pathlib.Path;G=P('/srv/android/asus-genuine-service-runtime');A=P('/srv/android/lineage24/out/target/product/p00a');d={'fixtures':{},'texts':{},'actual_installed':{},'actual_raw':{},'boot':{}}
def small(p,hashit=True):
 p=P(p)
 if not p.exists():return dict(path=str(p),exists=False,symlink=p.is_symlink())
 s=p.stat();r=dict(path=str(p),exists=True,bytes=s.st_size,mtime_ns=s.st_mtime_ns,mode=oct(stat.S_IMODE(s.st_mode)))
 if p.is_file()and hashit:assert s.st_size<32*1024**2;r['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
 return r
for rel in ['inputs/kernel-r7/Image','inputs/kernel-r7/config','inputs/boot-r9/init_first_stage','inputs/boot-r9/fstab.mt8163','run-boot-r9/seed-exec','run-boot-r9/initramfs.cpio.gz','run-boot-r9/data.ext4','run-boot-r9/system.ext4','inputs/observer-r5/observer','inputs/boot-r9/root/system/bin/firstboot-observer']:
 d['fixtures'][rel]=small(G/rel,not rel.endswith('.ext4'))
for p in [G/'source/seed_exec.c',G/'inputs/boot-r9/fstab.mt8163',G/'inputs/boot-r9/root/system/etc/init/hw/init.rc']:
 if p.is_file():d['texts'][str(p)]=p.read_text()
for rel in ['system/bin/apexd','system/bin/servicemanager','system/system_ext/bin/hwservicemanager','system/bin/hwservicemanager','system/bin/keystore2','system/vendor/bin/hw/android.hardware.keymaster@4.0-service','system/bin/boringssl_self_test32','system/bin/boringssl_self_test64','system/etc/security/apexkeys.txt','system/apex/com.android.runtime.apex','system/apex/com.android.adbd.capex','system/etc/init/hw/init.rc','system/etc/init/keystore2.rc','system/vendor/etc/init/ACCOUNT_REDACTED','system/etc/fstab.mt8163']:
 d['actual_installed'][rel]=small(A/rel,False)
 if rel.endswith('.rc')or 'fstab' in rel:
  p=A/rel
  if p.is_file():d['texts'][str(p)]=p.read_text()
boot=A/'boot.img';d['boot']=small(boot);b=boot.read_bytes();assert b[:8]==b'ANDROID!' and len(b)<16740352
ks,ka,rs,ra,ss,sa,ta,page=struct.unpack_from('<8I',b,8);assert page==2048 and ss==0 and rs<32*1024**2
ro=page+((ks+page-1)//page)*page;ram=b[ro:ro+rs];assert len(ram)==rs
if ram[:4]==bytes.fromhex('88168858'):ram=ram[512:]
z=zlib.decompressobj(31);raw=z.decompress(ram,32*1024**2);assert z.eof and not z.unconsumed_tail
entries={};pos=0
while True:
 h=raw[pos:pos+110];assert h[:6]==b'070701';f=[int(h[6+8*i:14+8*i],16)for i in range(13)];sz,ns=f[6],f[11];name=raw[pos+110:pos+110+ns-1].decode();pos=(pos+110+ns+3)//4*4;value=raw[pos:pos+sz];assert len(value)==sz;pos=(pos+sz+3)//4*4
 if name=='TRAILER!!!':break
 assert not name.startswith('/')and '..'not in name.split('/');entries[name]=(f,value)
d['boot'].update(kernel_bytes=ks,ramdisk_bytes=rs,ramdisk_sha256=hashlib.sha256(ram).hexdigest(),cpio_entries=len(entries),selected_entries={})
for name,(f,value)in entries.items():
 if name=='init'or 'fstab' in name or name.endswith('.prop'):
  row=dict(mode=oct(f[1]),uid=f[2],gid=f[3],bytes=len(value),sha256=hashlib.sha256(value).hexdigest());d['boot']['selected_entries'][name]=row
  if 'fstab'in name or name.endswith('.prop'):row['text']=value.decode(errors='replace')
d['boot']['unchanged_after_read']=small(boot)=={k:v for k,v in d['boot'].items()if k in ['path','exists','bytes','mtime_ns','mode','sha256']}
rawpath=P('/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw');d['raw_identity']=small(rawpath,False)
D=P('/srv/android/asus-full-system-observer-preparation-20261106/immutable/bin/debugfs');assert D.is_file();d['debugfs']=small(D)
env=os.environ.copy();env['LD_LIBRARY_PATH']='/srv/android/asus-full-system-observer-preparation-20261106/immutable/lib64'
commands=['ls -l system/apex','stat system/bin/boringssl_self_test32','stat system/bin/boringssl_self_test64','stat system/bin/apexd','stat system/bin/keystore2','stat system/vendor/bin/hw/android.hardware.keymaster@4.0-service','cat system/etc/init/hw/init.rc','cat system/etc/init/keystore2.rc','cat system/vendor/etc/init/ACCOUNT_REDACTED']
for cmd in commands:
 p=subprocess.run([str(D),'-R',cmd,str(rawpath)],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=10,env=env);assert len(p.stdout)+len(p.stderr)<65536;d['actual_raw'][cmd]=dict(exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
d['raw_identity_unchanged']=small(rawpath,False)==d['raw_identity'];d['no_new_fixture_built_or_launched']=True;print(json.dumps(d,indent=2))
