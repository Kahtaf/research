"""Fixed full-size host file builder/validator. No formatter target override."""
from pathlib import Path
import os,stat,struct,uuid,hashlib,json,subprocess,sys
R=Path('/srv/android/asus-internal-data-validation')
SIZE=11331268096; BLOCK=4096; BLOCKS=2766422; FS=BLOCKS*BLOCK; CHUNK=32*1024*1024
UUID='be11dc64-b759-40a3-af67-1236cc8cb655'
FEATURES='none,has_journal,ext_attr,dir_index,filetype,extent,sparse_super,large_file,uninit_bg,dir_nlink,extra_isize'
def need(v,msg):
 if not v:raise ValueError(msg)
def safe(path,existing=True):
 p=Path(path);need(p.is_absolute() and '..' not in p.parts and p.is_relative_to(R),'fixed host fixture only')
 for a in [*reversed(p.parents),p]:
  if a==p and not existing:continue
  s=a.lstat();need(not stat.S_ISLNK(s.st_mode),'symlink forbidden')
  need(stat.S_ISREG(s.st_mode) if a==p else stat.S_ISDIR(s.st_mode),'regular host file/directory only')
 return p
def new(path):
 p=safe(path,False);fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_NOFOLLOW,0o600)
 need(stat.S_ISREG(os.fstat(fd).st_mode),'regular file');return fd
def readat(f,offset,size):
 need(0<=offset<=SIZE-size,'read bounds');f.seek(offset);b=f.read(size);need(len(b)==size,'short read');return b
def inspect(path,pristine=True):
 p=safe(path);need(p.stat().st_size==SIZE,'partition size')
 with p.open('rb') as f:
  s=readat(f,1024,1024);u32=lambda off:struct.unpack_from('<I',s,off)[0];u16=lambda off:struct.unpack_from('<H',s,off)[0]
  need(u16(56)==0xef53,'magic');need((u32(92),u32(96),u32(100))==(0x2c,0x42,0x73),'features')
  need(u32(4)==BLOCKS and u32(336)==0 and u32(24)==2 and u32(20)==0,'block geometry')
  need(u32(8)==0 and u16(88)==256 and u32(32)==32768,'inode/reserved geometry')
  need(str(uuid.UUID(bytes=s[104:120]))==UUID and s[120:136].rstrip(b'\0')==b'A17DATA','identity')
  ipg=u32(40);ng=(BLOCKS+32767)//32768;need(u32(0)==ng*ipg and 0<ipg<=32768 and ipg%16==0,'inode count')
  need(u16(58)==1,'unclean filesystem');need(u32(224)==8,'journal inode')
  gdt=readat(f,BLOCK,ng*32);groups=[];tables=[]
  for i in range(ng):
   bb,ib,it=struct.unpack_from('<III',gdt,i*32);lo=i*32768;hi=min(lo+32768,BLOCKS);itn=ipg*256//BLOCK
   need(lo<=bb<hi and lo<=ib<hi and lo<=it and it+itn<=hi,'group bounds')
   need(bb!=ib and not it<=bb<it+itn and not it<=ib<it+itn,'metadata overlap')
   # Read both bitmaps and every inode-table byte, including the final group.
   for start,n in [(bb,1),(ib,1),(it,itn)]:readat(f,start*BLOCK,n*BLOCK)
   tables.append(it);groups.append(dict(group=i,start=lo,end=hi,block_bitmap=bb,inode_bitmap=ib,inode_table=it,inode_table_blocks=itn,flags=struct.unpack_from('<H',gdt,i*32+18)[0]))
  ino=readat(f,tables[0]*BLOCK+256,256);uid=struct.unpack_from('<H',ino,2)[0]|struct.unpack_from('<H',ino,120)[0]<<16;gid=struct.unpack_from('<H',ino,24)[0]|struct.unpack_from('<H',ino,122)[0]<<16;mode=struct.unpack_from('<H',ino,0)[0]
  if pristine:need((uid,gid,mode)==(0,0,0o40755),'root ownership/mode')
  need(readat(f,FS,SIZE-FS)==bytes(SIZE-FS),'nonzero tail')
 return dict(bytes=SIZE,filesystem_bytes=FS,blocks=BLOCKS,block_size=BLOCK,inode_size=256,inodes=ng*ipg,group_count=ng,groups=groups,root_uid=uid,root_gid=gid,root_mode=oct(mode),compat='0x2c',incompat='0x42',ro_compat='0x73',uuid=UUID,label='A17DATA',tail_zero_bytes=SIZE-FS)
def hashes(path):
 p=safe(path);need(p.stat().st_size==SIZE,'hash size');h=hashlib.sha256();chunks=[]
 with p.open('rb') as f:
  pos=0
  while pos<SIZE:
   b=f.read(min(CHUNK,SIZE-pos));need(bool(b),'hash short read');h.update(b);chunks.append(dict(offset=pos,size=len(b),sha256=hashlib.sha256(b).hexdigest()));pos+=len(b)
  need(not f.read(1),'hash extra bytes')
 return dict(bytes=SIZE,sha256=h.hexdigest(),chunk_bytes=CHUNK,chunks=chunks,sparse_semantics='Every logical raw byte is hashed, including zero-valued holes. Destination must materialize and verify all bytes.')
def command(argv,name,env=None):
 p=subprocess.run(argv,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env);(R/'evidence'/name).write_text(json.dumps(argv)+'\n'+p.stdout+f'\nexit={p.returncode}\n');need(p.returncode==0,name);return p.stdout
def build():
 pins=json.loads((R/'evidence/input-pins.json').read_text());tools={p['tool']:p for p in pins if 'tool' in p}
 for n in ['mke2fs','e2fsck','dumpe2fs','sha256sum']:
  t=tools[n];need(hashlib.sha256(Path(t['path']).read_bytes()).hexdigest()==t['sha256'],'tool changed '+n)
 command([tools['mke2fs']['path'],'-V'],'formatter-version.txt')
 p=R/'artifacts/A17DATA-pristine.raw';fd=new(p);os.ftruncate(fd,SIZE);os.fsync(fd);os.close(fd)
 args=[tools['mke2fs']['path'],'-t','ext4','-b','4096','-I','256','-m','0','-L','A17DATA','-U',UUID,'-O',FEATURES,'-E','nodiscard,lazy_itable_init=0,lazy_journal_init=0,root_owner=0:0','--',str(p),str(BLOCKS)]
 command(args,'formatter.txt',{**os.environ,'MKE2FS_CONFIG':str(R/'inputs/mke2fs.conf'),'E2FSPROGS_FAKE_TIME':'1793952000'})
 need(p.stat().st_size==SIZE,'formatter altered partition length')
 fd=os.open(safe(p),os.O_RDWR|os.O_NOFOLLOW);os.pwrite(fd,bytes(SIZE-FS),FS);os.fsync(fd);os.close(fd)
 command([tools['e2fsck']['path'],'-fn',str(p)],'pristine-e2fsck.txt')
 command([tools['dumpe2fs']['path'],str(p)],'pristine-dumpe2fs.txt')
 metadata=inspect(p);(R/'evidence/pristine-inspection.json').write_text(json.dumps(metadata,indent=2)+'\n')
 manifest=hashes(p);second=command([tools['sha256sum']['path'],str(p)],'pristine-independent-reread.txt').split()[0];need(second==manifest['sha256'],'independent full reread mismatch')
 manifest.update(path=str(p),independent_reread_sha256=second,formatter=tools['mke2fs'],formatter_argv=args,config_sha256=hashlib.sha256((R/'inputs/mke2fs.conf').read_bytes()).hexdigest(),uuid=UUID)
 p.chmod(0o400);d=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY);os.fsync(d);os.close(d)
 (R/'evidence/image-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({k:v for k,v in manifest.items() if k!='chunks'},indent=2))
if __name__=='__main__':
 need(sys.argv[1:]==['build'],'only fixed build supported');build()
