from pathlib import Path
import os,stat,subprocess as s,json,hashlib,struct,gzip,shutil,resource,datetime
R=Path('/srv/android/asus-r9-actual-early-runtime-20261106');G=Path('/srv/android/asus-genuine-service-runtime');I=R/'inputs';E=R/'evidence'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.environ['TMPDIR']=str(R/'tmp')
def h(b):return hashlib.sha256(b).hexdigest()
def ident(p):
 st=p.stat();return dict(path=str(p),dev=st.st_dev,inode=st.st_ino,bytes=st.st_size,mtime_ns=st.st_mtime_ns,ctime_ns=st.st_ctime_ns,mode=oct(stat.S_IMODE(st.st_mode)))
raw=Path('/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw');ri=ident(raw)
assert all(ri[k]==v for k,v in dict(dev=2049,inode=27263347,bytes=3753902080,mtime_ns=1794019280920581777,ctime_ns=1794019538990926800,mode='0o444').items()),ri
pins={}
for name,pin,size in [('kernel', '95a62a8bccd3085d682a89b6c74c7afd0961cebd1e3137b256229849920b549b',None),('config','c2ea1277e1574da39d1d55d31bde7bda439ab624561ad3c6a6f4730e38f57834',None),('boot','784d4dc565e7742ea607683d2a67d1fdb066764bddfa369895cbaaf6f048b435',9242624),('seed-exec','eddd78f4558e38ba1a1b5f2d9a8420111859e70a1d9c0d3b9cd837a4207ecf60',None)]:
 p={'kernel':G/'inputs/kernel-r7/Image','config':G/'inputs/kernel-r7/config','boot':Path('/srv/android/asus-r9-independent-packaging-r2/checks/UNTESTED-ROOT-ROUTE-FAILED-sdk37-combined-boot.img'),'seed-exec':G/'run-boot-r9/seed-exec'}[name];b=p.read_bytes();assert h(b)==pin and (size is None or len(b)==size);pins[name]={**ident(p),'sha256':h(b)}
 if name in ['boot','seed-exec']:shutil.copyfile(p,I/name)
b=(I/'boot').read_bytes();assert b[:8]==b'ANDROID!';ks,ka,rs,ra,ss,sa,ta,page=struct.unpack_from('<8I',b,8);assert page==2048 and ss==0;off=page+((ks+page-1)//page)*page;ram=b[off:off+rs];assert ram[:4]==bytes.fromhex('88168858') and ram[8:14]==b'ROOTFS';wrapper=ram[:512];ram=ram[512:];assert len(ram)==1520040 and h(ram)=='95f5c2a8aded2e081e30e72ebd37322a24aa895bbe7e334c79c1381bcd3fe240';(I/'actual-ramdisk.cpio.gz').write_bytes(ram);(I/'mtkrootfs-wrapper.bin').write_bytes(wrapper)
a=gzip.decompress(ram);pos=0;entries=[]
while True:
 head=a[pos:pos+110];assert head[:6]==b'070701';f=[int(head[6+8*i:14+8*i],16) for i in range(13)];size,ns=f[6],f[11];name=a[pos+110:pos+110+ns-1].decode();pos=(pos+110+ns+3)//4*4;val=a[pos:pos+size];pos=(pos+size+3)//4*4
 if name=='TRAILER!!!':break
 assert not name.startswith('/') and '..' not in name.split('/');entries.append((name,f,val))
assert len(entries)==14 and len({n for n,f,v in entries})==13
actualinit=next(v for n,f,v in entries if n=='init');assert h(actualinit)=='b2abeeb7dc01d884536dd38ebccd835a8589187a979cf84e51d78131ce800ed4';(I/'actual-init').write_bytes(actualinit)
# Change backend names only; all fstab options and comments stay byte exact.
def mapfstab(b):
 for src,dst in [(b'/dev/block/platform/soc/11230000.mmc/by-name/system',b'/dev/block/vdb'),(b'/dev/block/platform/soc/11230000.mmc/by-name/userdata',b'/dev/block/vda')]:
  assert b.count(src)==1;b=b.replace(src,dst)
 return b
bootfstab=next(v for n,f,v in entries if n=='fstab.mt8163');mapped=mapfstab(bootfstab);(I/'boot.fstab.original').write_bytes(bootfstab);(I/'boot.fstab').write_bytes(mapped)
d=json.loads((E/'inspection2.json').read_text());vendor=d['cat system/vendor/etc/fstab.mt8163']['stdout'].encode();(I/'vendor.fstab.original').write_bytes(vendor);(I/'vendor.fstab').write_bytes(mapfstab(vendor))
# Retained observer source, with all property writes removed. Diagnostic work runs asynchronously.
obs=(G/'source/observer.c').read_text();start=obs.index('errno=0;int rc=__system_property_set(');end=obs.index('read_path("/proc/mounts");',start);obs=obs[:start]+obs[end:];assert '__system_property_set' not in obs
obs=obs.replace('int main(void){','static int sample(void){');obs+='\nint main(void){setvbuf(stdout,NULL,_IONBF,0);for(int i=0;i<18;i++){printf("ACTUAL_RUNTIME_SAMPLE index=%d\\n",i);sample();sleep(5);}return 0;}\n';(R/'source/observer.c').write_text(obs)
cmd=json.loads(d['evidence/observer-compile.json'])['command'];out=[]
for x in cmd:
 x=x.replace(str(G/'source/observer.c'),str(R/'source/observer.c')).replace(str(G/'inputs/observer-r1/observer.d'),str(E/'observer.d')).replace(str(G/'inputs/boot-r2/root/system/bin/firstboot-observer'),str(I/'observer'))
 out.append(x)
commands=[]
def run(cmd,timeout=60):
 p=s.run(cmd,capture_output=True,text=True,timeout=timeout);commands.append(dict(command=cmd,rc=p.returncode,stdout=p.stdout,stderr=p.stderr));(E/'prepare-commands.json').write_text(json.dumps(commands,indent=2));assert p.returncode==0,p.stderr;return p
run(out)
rc='''service actual-runtime-observer /system/bin/actual-runtime-observer
    class core
    user shell
    group shell log readproc
    seclabel u:r:shell:s0
    disabled
    oneshot
    stdio_to_kmsg

on early-init
    start actual-runtime-observer
''';(I/'observer.rc').write_text(rc)
# QCOW2 v2: 64KiB clusters, four initial metadata clusters, explicit raw backing node in QEMU.
c=65536;l1=(ri['bytes']+c*(c//8)-1)//(c*(c//8));back=str(raw).encode();header=struct.pack('>IIQIIQIIQQIIQ',0x514649fb,2,72,len(back),16,ri['bytes'],0,l1,c*3,c,1,0,0);assert len(header)==72
with (I/'system.qcow2').open('xb') as f:
 f.write(header+back);f.seek(c);f.write(struct.pack('>Q',2*c));f.seek(2*c);f.write(struct.pack('>4H',1,1,1,1));f.truncate(4*c)
run(['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra','-Werror',str(R/'source/patcher.c'),'-o',str(I/'patcher')])
# Preserve every original CPIO entry's metadata except intentional init adapter and fstab content.
def cpio(entries):
 a=bytearray()
 for name,f,val in entries+[('TRAILER!!!',[0]*13,b'')]:
  f=f.copy();nb=name.encode()+b'\0';f[6]=len(val);f[11]=len(nb);a.extend(b'070701'+''.join(f'{v:08x}' for v in f).encode()+nb);a.extend(b'\0'*(-len(a)%4));a.extend(val);a.extend(b'\0'*(-len(a)%4))
 return gzip.compress(a,mtime=0)
def ent(n,b,mode=0o100644):return n,[1,mode,0,0,1,0,len(b),0,0,0,0,len(n)+1,0],b
prep=[ent(n,b,mode) for n,b,mode in [('init',(I/'patcher').read_bytes(),0o100755),('vendor.fstab',(I/'vendor.fstab').read_bytes(),0o100644),('observer',(I/'observer').read_bytes(),0o100755),('observer.rc',(I/'observer.rc').read_bytes(),0o100644)]]
(I/'patch-initramfs.cpio.gz').write_bytes(cpio(prep))
new=[];manifest=[]
for n,f,v in entries:
 orig=v
 if n=='init':v=(I/'seed-exec').read_bytes()
 if n=='fstab.mt8163':v=mapped
 new.append((n,f,v));manifest.append(dict(path=n,fields=f,before_sha256=h(orig),after_sha256=h(v),before_bytes=len(orig),after_bytes=len(v)))
new+=[ent('first-stage-init',actualinit,0o100750),ent('entropy.seed',os.urandom(64),0o100400)]
(I/'runtime-initramfs.cpio.gz').write_bytes(cpio(new));os.chmod(I/'runtime-initramfs.cpio.gz',0o600)
(E/'ramdisk-deltas.json').write_text(json.dumps({'original_entries':manifest,'added':[{'path':'first-stage-init','sha256':h(actualinit),'mode':'0100750','uid':0,'gid':0},{'path':'entropy.seed','bytes':64,'mode':'0100400','fresh_random':True,'value_and_hash_withheld':True}],'gzip_original_sha256':h(ram),'strip_wrapper_bytes':512},indent=2))
(E/'input-pins.json').write_text(json.dumps({'pins':pins,'raw':{**ri,'sha256_inherited':'baa69560ace09a478c902077d8ff926d7a079ecb9b9f1632e4c330169b243798'},'raw_hash_basis':'prior qualified mount plus exact unchanged identity; no additional fullraw hash','unchanged_identity':ident(raw)==ri,'new_files':{n:{'bytes':(I/n).stat().st_size,'sha256':h((I/n).read_bytes())} for n in ['observer','observer.rc','boot.fstab','vendor.fstab','patcher'] }},indent=2))
print(json.dumps({'status':'prepared','original_cpio_entries':len(entries),'raw_identity_unchanged':ident(raw)==ri,'qcow2_initial_bytes':(I/'system.qcow2').stat().st_size,'observer_no_property_setters':True}))
