#!/usr/bin/env python3
"""Fixed clean internal p26 ext4 recipe. Default prints plan. --fixture creates
one NEW bounded regular HOST file only. Never invokes a formatter on a device.
A future full raw image is reviewed/chunk-hashed, then provision-data streams it
through the same fixed p26 bounds gate; no arbitrary formatter command on target.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,stat,struct,subprocess
from rescue import PARTS,Refused,require
BLOCK_SIZE=4096
SIZE=PARTS['userdata']['sectors']*512
FEATURES='none,has_journal,ext_attr,dir_index,filetype,extent,sparse_super,large_file,uninit_bg,dir_nlink,extra_isize'
UUID='be11dc64-b759-40a3-af67-1236cc8cb655'

def recipe(path,blocks):
 return ['-t','ext4','-b','4096','-I','256','-m','0','-L','A17DATA','-U',UUID,
         '-O',FEATURES,'-E','nodiscard,lazy_itable_init=0,lazy_journal_init=0,root_owner=0:0','--',str(path),str(blocks)]
def inspect(path):
 with path.open('rb') as f:f.seek(1024);s=f.read(1024)
 require(struct.unpack_from('<H',s,56)[0]==0xef53,'ext4 superblock magic')
 compat,incompat,ro=struct.unpack_from('<III',s,92)
 # Exact deliberately selected legacy features. No encrypt/verity/64bit/checksum_seed/orphan_file.
 require(compat==0x2c and incompat==0x42 and ro==0x73,'unexpected ext4 feature set')
 require(struct.unpack_from('<I',s,24)[0]==2,'block size')
 with path.open('rb') as f:
  f.seek(4096);gd=f.read(32);table=struct.unpack_from('<I',gd,8)[0]
  f.seek(table*4096+256);inode=f.read(256)
 uid=struct.unpack_from('<H',inode,2)[0]|struct.unpack_from('<H',inode,120)[0]<<16
 gid=struct.unpack_from('<H',inode,24)[0]|struct.unpack_from('<H',inode,122)[0]<<16
 require(uid==gid==0 and struct.unpack_from('<H',inode,0)[0]==0o40755,'root directory owner/mode')
 return dict(root_uid=uid,root_gid=gid,root_mode="0755",block_size=4096,blocks=struct.unpack_from('<I',s,4)[0],compat=hex(compat),incompat=hex(incompat),ro_compat=hex(ro),encryption='plain ext4; no FBE/FDE')
def plan():
 return dict(mode='PLAN_ONLY',target='/dev/block/mmcblk0p26',geometry=PARTS['userdata'],partition_bytes=SIZE,
  filesystem_blocks=SIZE//BLOCK_SIZE,filesystem_bytes=SIZE//BLOCK_SIZE*BLOCK_SIZE,trailing_zero_bytes=SIZE%BLOCK_SIZE,
  features=FEATURES,formatter_arguments=recipe('REVIEWED_NEW_HOST_RAW_IMAGE',SIZE//BLOCK_SIZE),
  userdata_preservation_required=False,metadata_policy='Leave p20 unchanged for Android17. Stock rollback footer magic invalidation is a separate reviewed operation.',
  required=['Verified original BOOT/SYSTEM and original recovery backups','Independent authenticated dedicated recovery runtime restore proof','Fixed p26 alias/rdev/sysfs/GPT/CID and no mounts or dm holders','Parent reviewed complete raw image plus per-chunk SHA256; fill final 3584 bytes with zero','Read back ALL 11331268096 partition bytes','Installed fstab uses plain p26 ext4; no forceencrypt/fileencryption/formattable/resize/checkpoint flags'],
  stock_rollback='Restore original SYSTEM then BOOT while rescue p10 stays intact; provision fresh compatible plain ext4; separately review four-byte old footer magic invalidation before stock boot. Stock forceencrypt data reinitialization remains unproven on target.')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--fixture',type=Path);ap.add_argument('--evidence',type=Path);a=ap.parse_args()
 result=plan()
 if a.fixture:
  require(a.evidence is not None and not a.evidence.exists(),'new evidence required')
  require(not a.fixture.exists() and not a.fixture.is_symlink(),'fixture must be new')
  require('/dev' not in a.fixture.resolve().parents and not str(a.fixture.resolve()).startswith('/dev/'),'host file only')
  a.fixture.parent.mkdir(parents=True,exist_ok=True)
  fd=os.open(a.fixture,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
  require(stat.S_ISREG(os.fstat(fd).st_mode),'regular file required');os.ftruncate(fd,64*1024*1024);os.close(fd)
  binary=shutil.which('mke2fs');require(binary is not None,'local mke2fs missing')
  cmd=[binary,*recipe(a.fixture.resolve(),64*1024*1024//BLOCK_SIZE)]
  p=subprocess.run(cmd,capture_output=True,text=True,env={**os.environ,'E2FSPROGS_FAKE_TIME':'1793952000'})
  require(p.returncode==0,p.stderr)
  result.update(fixture=str(a.fixture),fixture_bytes=a.fixture.stat().st_size,fixture_superblock=inspect(a.fixture),formatter_sha256=hashlib.sha256(Path(binary).read_bytes()).hexdigest(),argv=cmd,stdout=p.stdout,stderr=p.stderr,target_execution=False)
  a.evidence.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
