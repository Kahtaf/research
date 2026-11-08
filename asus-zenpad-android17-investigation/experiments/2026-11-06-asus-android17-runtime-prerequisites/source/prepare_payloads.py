from pathlib import Path
import subprocess as s,hashlib,json,zipfile,struct,shutil
R=Path('/srv/android/asus-android17-runtime-prereqs');I=R/'inputs';T=Path('/srv/android/lineage24')
for name in ['fsck.erofs','avbtool']:
 src=T/'out/host/linux-x86/bin'/name; data=src.read_bytes(); assert data==src.read_bytes();dst=I/name; dst.write_bytes(data);dst.chmod(0o755)
 (R/'evidence'/f'{name}.sha256').write_text(hashlib.sha256(data).hexdigest()+'\n')
payloads=[]; (I/'disk-root').mkdir(exist_ok=True)
for name in ['adbd','google']:
 apex=I/(name+'.apex'); image=I/(name+'.img')
 with zipfile.ZipFile(apex) as z:
  info=z.getinfo('apex_payload.img');assert info.compress_type==0
  with apex.open('rb') as f:
   f.seek(info.header_offset); header=f.read(30)
  offset=info.header_offset+30+sum(struct.unpack('<HH',header[26:30])); assert offset%4096==0
 extract=I/(name+'-extracted');extract.mkdir(exist_ok=True)
 cmd=[str(I/'fsck.erofs'),'--extract='+str(extract),str(image)]
 p=s.run(cmd,stdout=s.PIPE,stderr=s.STDOUT,text=True)
 (R/'evidence'/f'{name}-host-extract.txt').write_text(p.stdout+f'\nexit={p.returncode}\n');assert p.returncode==0
 material=[]
 for f in sorted(extract.rglob('*')):
  if f.is_file() and not f.is_symlink(): material.append({'path':str(f.relative_to(extract)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size})
 avb=s.run([str(I/'avbtool'),'info_image','--image',str(image)],stdout=s.PIPE,stderr=s.STDOUT,text=True)
 (R/'evidence'/f'{name}-avb.txt').write_text(avb.stdout+f'\nexit={avb.returncode}\n');assert avb.returncode==0
 verify=s.run([str(I/'avbtool'),'verify_image','--image',str(image)],stdout=s.PIPE,stderr=s.STDOUT,text=True)
 (R/'evidence'/f'{name}-avb-verify.txt').write_text(verify.stdout+f'\nexit={verify.returncode}\n')
 def val(field):
  return next(line.split(':',1)[1].strip().split()[0] for line in avb.stdout.splitlines() if line.strip().startswith(field+':'))
 rec={'name':name,'apex_sha256':hashlib.sha256(apex.read_bytes()).hexdigest(),'image_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'offset':offset,'size':info.file_size,'files':material,'avb_signature_verified_embedded_key':verify.returncode==0}
 rec['verity']={k:val(k) for k in ['Image Size','Tree Offset','Tree Size','Data Block Size','Hash Block Size','Hash Algorithm','Root Digest','Salt','Version of dm-verity']}
 payloads.append(rec)
 shutil.copyfile(apex,I/'disk-root'/(name+'.apex'))
(R/'evidence/payload-manifest.json').write_text(json.dumps(payloads,indent=2)+'\n')
disk=R/'artifacts/data-base.ext4';assert not disk.exists()
with disk.open('wb') as f:f.truncate(512*1024*1024)
cmd=['/usr/sbin/mke2fs','-t','ext4','-F','-b','4096','-O','^metadata_csum,^64bit,^orphan_file','-E','lazy_itable_init=0,lazy_journal_init=0','-d',str(I/'disk-root'),str(disk)]
p=s.run(cmd,stdout=s.PIPE,stderr=s.STDOUT,text=True);(R/'evidence/ext4-create.txt').write_text(json.dumps(cmd)+'\n'+p.stdout+f'\nexit={p.returncode}\n');assert p.returncode==0
p=s.run(['/usr/sbin/dumpe2fs','-h',str(disk)],stdout=s.PIPE,stderr=s.STDOUT,text=True);(R/'evidence/ext4-superblock.txt').write_text(p.stdout)
print('payloads',[(p['name'],len(p['files']),p['verity']) for p in payloads])
