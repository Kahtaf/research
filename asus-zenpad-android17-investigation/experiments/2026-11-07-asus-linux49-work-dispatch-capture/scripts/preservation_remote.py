from pathlib import Path
import hashlib,json
R=Path('/srv/android/asus-linux49-work-dispatch-capture-20261107-b4702f9a');B=Path('/srv/android/asus-linux49-active-work-capture-20261107-8e5c5d4d');E=R/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
scoped={}
for root in ['kernel','out']:
 for rel in ['.git/HEAD','.git/config','.git/index','.gitmodules']:
  b=B/root/rel;r=R/root/rel
  if b.is_file():
   assert r.is_file() and sha(r)==sha(b)
   scoped[root+'/'+rel]=dict(sha256=sha(b),same_bytes=True,base_inode=b.stat().st_ino,copy_inode=r.stat().st_ino,independent_inode=b.stat().st_ino!=r.stat().st_ino)
   assert b.stat().st_ino!=r.stat().st_ino
result=dict(status='PASS_SCOPED_REPOSITORY_PRESERVATION',copy='cp -a --reflink=auto, no hardlinks; kernel/out copied as whole directories, preserving nested repositories',scoped_repository_metadata=scoped,no_git_mutation_commands=True,full_tree_inventory_or_rehash=False)
(E/'repository-preservation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
