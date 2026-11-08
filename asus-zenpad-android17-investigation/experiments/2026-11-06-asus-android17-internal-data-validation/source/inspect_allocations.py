"""Additional pristine extents/journal/eager-initialization audit, read-only."""
from image import *
p=R/'artifacts/A17DATA-pristine.raw';meta=inspect(p);out={}
with p.open('rb') as f:
 def inode(n):
  sb=readat(f,1024,1024);ipg=struct.unpack_from('<I',sb,40)[0];g,idx=divmod(n-1,ipg)
  return readat(f,meta['groups'][g]['inode_table']*BLOCK+idx*256,256)
 def extents(data,expected_depth=None,visited=None):
  if visited is None:visited=set()
  magic,n,cap,depth=struct.unpack_from('<HHHH',data);need(magic==0xf30a and n<=cap and 12+n*12<=len(data),'extent header')
  need(depth<=5 and (expected_depth is None or depth==expected_depth),'extent depth');result=[]
  for k in range(n):
   off=12+k*12;logical=struct.unpack_from('<I',data,off)[0]
   if depth:
    lo,hi=struct.unpack_from('<IH',data,off+4);block=lo+(hi<<32);need(0<block<BLOCKS and block not in visited,'extent index bounds/cycle');visited.add(block);result+=extents(readat(f,block*BLOCK,BLOCK),depth-1,visited)
   else:
    length,hi,lo=struct.unpack_from('<HHI',data,off+4);need(0<length<=32768,'initialized extent length');block=lo+(hi<<32);need(0<block and block+length<=BLOCKS,'extent data bounds');result.append(dict(logical=logical,start=block,blocks=length))
  return result
 for number,name in [(2,'root'),(8,'journal')]:
  i=inode(number);mode=struct.unpack_from('<H',i)[0];flags=struct.unpack_from('<I',i,32)[0];need(flags&0x80000,'extent inode required');size=struct.unpack_from('<I',i,4)[0]+(struct.unpack_from('<I',i,108)[0]<<32);e=extents(i[40:100]);need(sum(x['blocks'] for x in e)*BLOCK==size,'inode extent size');ordered=sorted(e,key=lambda x:x['logical']);logical=0
  for x in ordered:need(x['logical']==logical,'extent logical gap');logical+=x['blocks']
  out[name]=dict(inode=number,mode=oct(mode),bytes=size,extents=e)
 need(out['root']['bytes']==4096,'root size');need(out['journal']['mode']=='0o100600','journal mode')
 first=True;zeroed=0
 for e in sorted(out['journal']['extents'],key=lambda x:x['logical']):
  for n in range(e['blocks']):
   b=readat(f,(e['start']+n)*BLOCK,BLOCK)
   if first:
    magic,kind,sequence=struct.unpack_from('>III',b);need(magic==0xc03b3998 and kind==4,'JBD2 journal superblock');need(struct.unpack_from('>I',b,12)[0]==4096,'journal block size');out['journal']['jbd2_magic']=hex(magic);first=False
   else:need(b==bytes(BLOCK),'journal not eagerly zeroed');zeroed+=1
 out['journal']['zeroed_blocks_after_header']=zeroed
 need(all(g['flags']&4 for g in meta['groups']),'inode tables not marked initialized');out['all_inode_tables_zeroed_flag']=True
cmd=['debugfs','-R','ls -l /',str(p)];q=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);need(q.returncode==0,'debugfs');(R/'evidence/pristine-root-list.txt').write_text(json.dumps(cmd)+'\n'+q.stdout);need('lost+found' in q.stdout,'missing lost+found')
out['passed']=True;(R/'evidence/pristine-allocations.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
