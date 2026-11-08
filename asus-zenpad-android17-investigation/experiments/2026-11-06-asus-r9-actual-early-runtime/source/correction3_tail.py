import subprocess as s,struct,gzip,json,sys,os
R=Path('/srv/android/asus-r9-actual-early-runtime-20261106');I=R/'inputs';E=R/'evidence'
(I/'system.qcow2').rename(I/'system-failed-prep-1.qcow2')
c=65536;raw='/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw';size=3753902080;back=raw.encode();l1=(size+c*(c//8)-1)//(c*(c//8))
with (I/'system.qcow2').open('xb') as f:
 f.write(struct.pack('>IIQIIQIIQQIIQ',0x514649fb,2,72,len(back),16,size,0,l1,3*c,c,1,0,0)+back);f.seek(c);f.write(struct.pack('>Q',2*c));f.seek(2*c);f.write(struct.pack('>4H',1,1,1,1));f.truncate(4*c)
p=s.run(['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra','-Werror',str(R/'source/patcher.c'),'-o',str(I/'patcher')],capture_output=True,text=True,timeout=60);(E/'patcher-correction3-compile.json').write_text(json.dumps(dict(rc=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0,p.stderr
# Existing prepared runtime initramfs and fresh entropy are preserved. Only offline patch preparation changes.
a=bytearray()
for n,data,mode in [('init',(I/'patcher').read_bytes(),0o100755),('vendor.fstab',(I/'vendor.fstab').read_bytes(),0o100644),('observer',(I/'observer').read_bytes(),0o100755),('observer.rc',(I/'observer.rc').read_bytes(),0o100644),('TRAILER!!!',b'',0)]:
 nb=n.encode()+b'\0';vals=[1,mode,0,0,1,0,len(data),0,0,0,0,len(nb),0];a+=b'070701'+''.join(f'{v:08x}' for v in vals).encode()+nb;a+=b'\0'*(-len(a)%4);a+=data;a+=b'\0'*(-len(a)%4)
(I/'patch-initramfs-before-correction3.cpio.gz').write_bytes((I/'patch-initramfs.cpio.gz').read_bytes());(I/'patch-initramfs.cpio.gz').write_bytes(gzip.compress(a,mtime=0))
sys.argv=['execute.py','patch'];exec(compile((R/'source/execute.py').read_bytes(),str(R/'source/execute.py'),'exec'))
assert 'COW_PATCH_COMPLETE files_changed=1 files_added=2' in (R/'run-patch-2/serial.log').read_text()
exec(compile((R/'source/cow_verify.py').read_bytes(),str(R/'source/cow_verify.py'),'exec'))
