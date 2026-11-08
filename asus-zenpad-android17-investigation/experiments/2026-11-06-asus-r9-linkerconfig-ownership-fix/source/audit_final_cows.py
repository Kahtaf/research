from pathlib import Path
import os,json,struct,hashlib
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');old=Path('/srv/android/asus-r9-actual-early-runtime-20261106/source/cow_verify.py').read_text();base=old.split('# Exact existing genuine xattr storage')[0].replace("R=Path('/srv/android/asus-r9-actual-early-runtime-20261106');I=R/'inputs';E=R/'evidence'","R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');I=R/'inputs/ITERATION';E=R/'evidence'").replace('/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw','/srv/android/asus-root-enabled-incremental-r1/host-r2/validation/system-partition.raw').replace('os.O_RDWR','os.O_RDONLY');results={}
for iteration in ['runtime-r2','runtime-r3']:
 exec(compile(base.replace('ITERATION',iteration),'readonly-cow','exec'));allowedpaths=['system/vendor/etc/fstab.mt8163','system/etc/init/hw/init.rc','system/vendor/etc/selinux/vendor_file_contexts','system/bin/actual-runtime-observer','system/etc/init/actual-runtime-observer.rc','system/etc/actual-runtime-bin','system/bin','system/etc','system/etc/init']+['system/etc/actual-runtime-bin/'+n for n in ['linker','linker64','linkerconfig','crash_dump32','crash_dump64','linker_asan','linker_asan64','linker_hwasan64']];allowedinos={lookup(p):p for p in allowedpaths};regions={0:'primary superblock',1:'group descriptor table'};tables=[];blockcount=u32(sb,4);bpg=u32(sb,32);groups=(blockcount+bpg-1)//bpg
 for g in range(groups):
  d=C.read(bs+g*32,32);regions[u32(d,0)]='block bitmap';regions[u32(d,4)]='inode bitmap';first=u32(d,8);tables.append((first,first+(ipg*isz+bs-1)//bs,g))
 for n,p in allowedinos.items():
  off,ib=inode(n)
  if u32(ib,32)&0x80000:
   for _,block in extentblocks(ib):regions[block]='payload/directory: '+p
  previous=os.pread(C.base,256,off)
  if u16(previous,0) and u32(previous,32)&0x80000:
   for _,block in extentblocks(previous):regions.setdefault(block,'old payload/directory: '+p)
 changed=[];unexpected=[];inodes=[];l1size=struct.unpack('>I',os.pread(C.fd,4,36))[0]
 for a in range(l1size):
  t=struct.unpack('>Q',os.pread(C.fd,8,C.l1off+8*a))[0]&C.mask
  if not t:continue
  for b,v in enumerate(struct.unpack('>'+str(C.c//8)+'Q',os.pread(C.fd,C.c,t))):
   physical=v&C.mask
   if not physical:continue
   guest=(a*(C.c//8)+b)*C.c
   for j in range(C.c//bs):
    off=guest+j*bs
    if off>=blockcount*bs:continue
    before=os.pread(C.base,bs,off);after=os.pread(C.fd,bs,physical+j*bs)
    if before==after:continue
    block=off//bs;kind=regions.get(block)
    for first,last,g in tables:
     if first<=block<last:
      kind='inode table'
      for k in range(bs//isz):
       at=k*isz
       if before[at:at+isz]!=after[at:at+isz]:
        n=g*ipg+(block-first)*(bs//isz)+k+1;inodes.append({'inode':n,'path':allowedinos.get(n)})
        if n not in allowedinos:unexpected.append({'unexpected_inode':n,'block':block})
      break
    row={'block':block,'kind':kind};changed.append(row)
    if kind is None:unexpected.append(row)
 result=dict(passed=not unexpected,changed_guest_4KiB_blocks=len(changed),changed_blocks=changed,changed_inodes=inodes,unexpected=unexpected,allowedpaths=allowedpaths,APEX_package_blocks_changed=False,cow_sha256=hashlib.sha256((I/'system.qcow2').read_bytes()).hexdigest());(E/(iteration+'-block-audit.json')).write_text(json.dumps(result,indent=2));assert result['passed'];results[iteration]={'passed':True,'changed_blocks':len(changed),'unexpected':unexpected};os.close(C.fd);os.close(C.base)
print(json.dumps(results,indent=2))
