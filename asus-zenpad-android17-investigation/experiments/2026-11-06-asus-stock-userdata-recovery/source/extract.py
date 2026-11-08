from pathlib import Path
import hashlib,json,struct,zipfile
from bootformat_reference import parse_cpio,ungzip,align
from ext4_reference import Ext4
S=Path(__file__).resolve().parents[1]; W=S.parent
out=S/'inputs'; records=[]
def save(name,b,origin):
 p=out/name;p.write_bytes(b);records.append(dict(file=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),origin=origin))
def ramdisk(kind,pin):
 base=W/'2026-11-05-asus-boot-access-audit/artifacts/device-backup'
 a=(base/'initial'/f'{kind}.bin').read_bytes(); b=(base/'verify'/f'{kind}.bin').read_bytes()
 assert a==b and hashlib.sha256(a).hexdigest()==pin
 assert a[:8]==b'ANDROID!';ks,_,rs,_,ss,_,_,page=struct.unpack_from('<8I',a,8)
 assert page==2048 and ss==0
 ro=page+align(ks);r=a[ro:ro+rs];assert r[:4]==bytes.fromhex('88168858')
 entries=parse_cpio(ungzip(r[512:])[0])
 for name,(_,_,_,value) in entries.items():
  if name.endswith('.rc') or name in ['fstab.mt8163','etc/recovery.fstab','default.prop','init','sbin/recovery']:
   save(kind+'__'+name.replace('/','_'),value,str(base/'initial'/f'{kind}.bin')+'#'+pin+':'+name)
ramdisk('recovery','902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20')
ramdisk('boot','7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316')
p=W/'2026-11-06-asus-local-stock-rollback/artifacts/stock-rollback/system.img'
e=Ext4(p)
for path in ['build.prop','bin/vold','etc/init/vold.rc','etc/init/vdc.rc','bin/make_ext4fs','bin/e2fsck','etc/recovery-resource.dat','bin/recovery','bin/uncrypt']:
 try:n=e.lookup(path)
 except KeyError:continue
 i=e.inode(n);sz=struct.unpack_from('<I',i,4)[0]+(struct.unpack_from('<I',i,108)[0]<<32);assert sz<=16*1024*1024
 value=bytearray(sz)
 for logical,length,physical in e.extents(i[40:100]):
  a=logical*e.bs;count=min(length*e.bs,sz-a)
  for delta in range(0,count,1024*1024):
   piece=e.read(physical*e.bs+delta,min(1024*1024,count-delta));value[a+delta:a+delta+len(piece)]=piece
 save('system__'+path.replace('/','_'),value,str(p)+':'+path+' (selected reads; existing whole-image receipt trusted)')
e.f.close()
with zipfile.ZipFile(W/'2026-11-05-asus-latest-android-feasibility/downloads/UL-P00A_2-WW-5.3.20.0-user.zip') as z:
 save('oem-updater-script.txt',z.read('META-INF/com/google/android/updater-script'),'pinned public OEM ZIP; selected member only, never executed')
(S/'evidence/input-pins.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(dict(selected_files=len(records),bytes=sum(x['bytes'] for x in records))))
