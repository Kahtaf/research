from pathlib import Path
import os,subprocess,struct,json,sys
from image import R,SIZE,FS,new,safe,inspect,need
O=R/'tests/negative-r1';O.mkdir();p=O/'mutant.raw';fd=new(p);os.close(fd);subprocess.run(['cp','--reflink=auto','--sparse=always',str(R/'artifacts/A17DATA-pristine.raw'),str(p)],check=True);p.chmod(0o600)
results=[]
def rejected(name,fn):
 try:fn()
 except (ValueError,FileExistsError) as e:results.append(dict(test=name,rejected=True,reason=str(e)));return
 raise AssertionError('accepted invalid '+name)
def mutate(name,offset,data):
 with p.open('r+b') as f:f.seek(offset);old=f.read(len(data));f.seek(offset);f.write(data);f.flush()
 rejected(name,lambda:inspect(p))
 with p.open('r+b') as f:f.seek(offset);f.write(old)
base=inspect(p);root=base['groups'][0]['inode_table']*4096+256
mutate('forbid_64bit',1024+96,struct.pack('<I',0xc2))
mutate('forbid_encrypt',1024+96,struct.pack('<I',0x10042))
mutate('forbid_verity',1024+100,struct.pack('<I',0x8073))
mutate('root_uid',root+2,struct.pack('<H',1000))
mutate('root_permissions',root,struct.pack('<H',0o40777))
mutate('block_count',1024+4,struct.pack('<I',2766421))
mutate('inode_size',1024+88,struct.pack('<H',128))
mutate('last_group_inode_table_outside',4096+84*32+8,struct.pack('<I',2766420))
mutate('nonzero_partition_tail',FS,b'\x01')
with p.open('r+b') as f:f.truncate(SIZE-512)
rejected('short_partition',lambda:inspect(p))
with p.open('r+b') as f:f.truncate(SIZE+512)
rejected('long_partition',lambda:inspect(p))
with p.open('r+b') as f:f.truncate(SIZE)
rejected('output_collision',lambda:new(p))
link=O/'symlink.raw';link.symlink_to(p);rejected('symlink_input',lambda:safe(link));rejected('symlink_output',lambda:new(link))
dirlink=O/'linked';dirlink.symlink_to(O,target_is_directory=True);rejected('symlink_parent',lambda:new(dirlink/'new.raw'))
rejected('device_path',lambda:new(Path('/dev/null')))
rejected('traversal',lambda:new(O/'..'/'escaped.raw'))
rejected('directory_input',lambda:safe(O))
inspect(p);(R/'evidence/negative-tests.json').write_text(json.dumps(dict(passed=True,cases=results),indent=2)+'\n');print(json.dumps(results,indent=2))
