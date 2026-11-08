"""Build reviewed raw-image manifests. Default is PLAN ONLY.
Only complete fixed-size ordinary files; Android sparse images are rejected.
BOOT is available only after corresponding whole SYSTEM hash matches."""
import argparse,hashlib,json,os,stat,struct
from pathlib import Path
CHUNK=1048576
GEOMETRY={9:16740352,25:3753902080,26:11331268096}
ROLES=('original_system','original_boot','install_system','install_boot','provision_userdata')
def digest_file(path,length):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|getattr(os,'O_NOATIME',0))
 try:
  st=os.fstat(fd)
  if not stat.S_ISREG(st.st_mode) or st.st_size!=length:raise ValueError('exact full raw length required: '+str(path))
  full=hashlib.sha256();chunks=[]
  for offset in range(0,length,CHUNK):
   size=min(CHUNK,length-offset);b=os.pread(fd,size,offset)
   if len(b)!=size:raise ValueError('short raw input read')
   if not chunks and b[:4]==bytes.fromhex('3aff26ed'):raise ValueError('Android sparse input forbidden')
   full.update(b);chunks.append(hashlib.sha256(b).digest())
  after=os.fstat(fd)
  if (after.st_ino,after.st_dev,after.st_size,after.st_mtime_ns,after.st_ctime_ns)!=(st.st_ino,st.st_dev,st.st_size,st.st_mtime_ns,st.st_ctime_ns):raise ValueError('input changed while hashing')
  return full.digest(),chunks
 finally:os.close(fd)
def build(review, digest=digest_file):
 required={'cid_sha256','primary_gpt_sha256','backup_gpt_sha256','images','approvals'}
 if set(review)!=required:raise ValueError('unknown or missing review fields')
 if not isinstance(review['cid_sha256'],str) or len(review['cid_sha256'])!=64 or any(c not in '0123456789abcdef' for c in review['cid_sha256']):raise ValueError('CID SHA256 must hash lowercase32hex without newline')
 approvals=review['approvals']
 needed={'durable_original_system_backup','durable_original_boot_backup','durable_original_recovery_backup','independent_rescue_review'}
 if 'provision_userdata' in review['images']:needed|={'clean_internal_data','factory_wifi_bt_preserved_locally','p26_provision_reviewed'}
 if set(approvals)!=needed or not all(v is True for v in approvals.values()):raise ValueError('parent backup/review approvals missing')
 if review['primary_gpt_sha256']!='f87e70586706b06d029a2bc8521f1b8ae9176873cba1e5b4281cbaca816742ae' or review['backup_gpt_sha256']!='2bf991125a74bf360d0cf4eb217df369ba2f78acf3dd312f26dc7695d2f31784':raise ValueError('exact saved GPT pair required')
 rows=review['images']
 if list(rows) not in [list(ROLES[:2]),list(ROLES[:4]),list(ROLES)]:raise ValueError('ordered original pair, optionally install pair')
 def shahex(h):
  if len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise ValueError('invalid SHA256')
  return bytes.fromhex(h)
 b=b'ASUSR002'+struct.pack('<II',2,len(rows))+shahex(review['cid_sha256'])+shahex(review['primary_gpt_sha256'])+shahex(review['backup_gpt_sha256'])
 evidence=[]
 for index,(role,row) in enumerate(rows.items()):
  if set(row)!={'path','sha256'}:raise ValueError('image fields')
  part=26 if index==4 else 9 if index%2 else 25;size=GEOMETRY[part]
  full,chunks=digest(row['path'],size)
  if index==1 and full.hex()!='7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316':raise ValueError('original BOOT must match both saved stock backups')
  if full!=shahex(row['sha256']):raise ValueError('reviewed hash mismatch')
  b+=struct.pack('<IIQ',index,part,size)+full+struct.pack('<I',len(chunks))+b''.join(chunks)
  evidence.append(dict(role=role,part=part,size=size,sha256=full.hex(),chunks=len(chunks)))
 return b,evidence
if __name__ == '__main__':
 raise SystemExit('Library only; use build_manifest.py (PLAN_ONLY by default).')
