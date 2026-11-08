from pathlib import Path
import json,struct,os,hashlib
R=Path('/srv/android/asus-r9-actual-early-runtime-20261106')
# Reuse only read/parse definitions; the mutation tail is deliberately excluded.
s=(R/'source/cow_verify.py').read_text().split('# Exact existing genuine xattr storage')[0].replace('os.O_RDWR','os.O_RDONLY');exec(compile(s,'cow_readonly_definitions','exec'))
allowedpaths=['system/vendor/etc/fstab.mt8163','system/bin/actual-runtime-observer','system/etc/init/actual-runtime-observer.rc','system/bin','system/etc/init']
allowedinos={lookup(p):p for p in allowedpaths};regions={};inodetables=[]
blockcount=u32(sb,4);bpg=u32(sb,32);groups=(blockcount+bpg-1)//bpg
regions[0]='primary superblock';regions[1]='group descriptor table'
for g in range(groups):
 d=C.read(bs+g*32,32);regions[u32(d,0)]='block bitmap';regions[u32(d,4)]='inode bitmap';first=u32(d,8);cnt=(ipg*isz+bs-1)//bs;inodetables.append((first,first+cnt,g))
for n,p in allowedinos.items():
 _,ib=inode(n)
 for logical,block in extentblocks(ib):regions[block]='payload or directory: '+p
 # Include any old fstab/directory extents as well.
 off,_=inode(n);old=os.pread(C.base,256,off)
 if u16(old,0) and u32(old,32)&0x80000:
  for logical,block in extentblocks(old):regions.setdefault(block,'old payload or directory: '+p)
changed=[];unknown=[];inodechanges=[];l1size=struct.unpack('>I',os.pread(C.fd,4,36))[0]
for l1 in range(l1size):
 table=struct.unpack('>Q',os.pread(C.fd,8,C.l1off+8*l1))[0]&C.mask
 if not table:continue
 vals=struct.unpack('>'+str(C.c//8)+'Q',os.pread(C.fd,C.c,table))
 for l2,v in enumerate(vals):
  phy=v&C.mask
  if not phy:continue
  guest=(l1*(C.c//8)+l2)*C.c
  for j in range(C.c//bs):
   off=guest+j*bs
   if off>=blockcount*bs:continue
   before=os.pread(C.base,bs,off);after=os.pread(C.fd,bs,phy+j*bs)
   if before==after:continue
   block=off//bs;kind=regions.get(block)
   for first,last,g in inodetables:
    if first<=block<last:
     kind='inode table';inos=[]
     for k in range(bs//isz):
      a=k*isz
      if before[a:a+isz]!=after[a:a+isz]:
       n=g*ipg+(block-first)*(bs//isz)+k+1;inos.append(n)
       inodechanges.append(dict(inode=n,path=allowedinos.get(n),changed_byte_offsets=[q for q in range(isz) if before[a+q]!=after[a+q]]))
       if n not in allowedinos:unknown.append(dict(block=block,unexpected_inode=n))
     break
   row=dict(block=block,kind=kind,before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest());changed.append(row)
   if kind is None:unknown.append(row)
d=dict(passed=not unknown,changed_guest_4KiB_blocks=len(changed),changed_blocks=changed,changed_inodes=inodechanges,unexpected=unknown,allowed_file_paths=allowedpaths,base_open_flags='O_RDONLY|O_NOFOLLOW',cow_readonly=True)
(R/'evidence/cow-block-audit.json').write_text(json.dumps(d,indent=2));print(json.dumps({k:v for k,v in d.items() if k not in ['changed_blocks','changed_inodes']},indent=2))
