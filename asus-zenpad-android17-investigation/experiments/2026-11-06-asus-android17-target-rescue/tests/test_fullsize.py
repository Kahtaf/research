"""Real Linux ordinary-file/socket run at exact production lengths.
Only test_server_full has the regular-file backend. No target/device I/O."""
from pathlib import Path
import hashlib,json,os,socket,struct,subprocess,sys,time
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'))
import client
C=1048576
name=sys.argv[1] if len(sys.argv)>1 else 'r2';assert name.startswith('r') and name[1:].isdigit();root=R/('artifacts/fullsize-'+name);root.mkdir();begin=time.monotonic()
def put(p,b):
 f=root/p.lstrip('/');f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
def sparse(p,n):
 f=root/p.lstrip('/');f.parent.mkdir(parents=True,exist_ok=True)
 with f.open('xb') as w:w.truncate(n)
def zero_hash(n):
 h=hashlib.sha256();z=bytes(C)
 for off in range(0,n,C):h.update(z[:min(C,n-off)])
 return h.digest()
sizes={0:15634268160,9:16740352,10:16740352,25:3753902080}
names={9:'boot',10:'recovery',25:'system'};starts={0:0,9:127488,10:160184,25:1072424}
for part,size in sizes.items():
 node='/dev/block/mmcblk0'+('p'+str(part) if part else '');sparse(node,size)
 base='/sys/dev/block/179:'+str(part);put(base+'/dev',f'179:{part}'.encode());put(base+'/start',str(starts[part]).encode());put(base+'/size',str(size//512).encode());(root/(base+'/holders').lstrip('/')).mkdir()
 if part:
  p=root/'dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name'/names[part];p.parent.mkdir(parents=True,exist_ok=True);p.symlink_to(root/node.lstrip('/'))
put('/sys/fs/selinux/enforce',b'1');put('/sys/class/block/mmcblk0/device/cid',b'0'*32);put('/proc/self/mountinfo',b'');(root/'dev/rescue-state').mkdir()
b=b'ASUSR002'+struct.pack('<II',2,2)+hashlib.sha256(b'0'*32).digest()+zero_hash(17408)+zero_hash(16896)
for index,part in enumerate([25,9]):
 size=sizes[part];chunks=[zero_hash(min(C,size-off)) for off in range(0,size,C)]
 b+=struct.pack('<IIQ',index,part,size)+zero_hash(size)+struct.pack('<I',len(chunks))+b''.join(chunks)
put('/rescue.manifest',b)
sparse('/reviewed-system.raw',sizes[25])
target=root/'dev/block/mmcblk0p25'
with target.open('r+b') as f:
 f.write(b'X'*C);f.flush();os.fsync(f.fileno())
p=subprocess.Popen([str(R/'artifacts/test_server_full'),str(root),'none'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
assert p.stdout.readline().startswith('READY')
try:
 reviewed_sha=zero_hash(sizes[25]).hex();p10sha=zero_hash(sizes[10]);prepared=client.prepare_image(b,0,root/'reviewed-system.raw',reviewed_sha)
 s=socket.socket(socket.AF_UNIX);s.connect(str(root/'server.sock'))
 with s,(R/('evidence/fullsize-'+name+'.jsonl')).open('x') as evidence:
  client.write_image(s.fileno(),b,p10sha,0,root/'reviewed-system.raw',reviewed_sha,evidence,prepared=prepared)
 with target.open('rb') as f:
  sha=hashlib.file_digest(f,'sha256').digest()
 assert sha==zero_hash(sizes[25])
 rows=[json.loads(line) for line in (R/('evidence/fullsize-'+name+'.jsonl')).read_text().splitlines()]
 result=dict(passed=True,bytes=sizes[25],sha256=sha.hex(),chunks=sum('chunk' in r for r in rows),writes=sum('chunk' in r and not r['skipped'] for r in rows),skips=sum('chunk' in r and r['skipped'] for r in rows),elapsed_seconds=time.monotonic()-begin,real_linux_file_socket=True,target_backend=False)
 assert result['chunks']==3580 and result['writes']==1 and result['skips']==3579
 (R/('evidence/fullsize-'+name+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
finally:
 p.terminate();out,err=p.communicate();(R/('evidence/fullsize-'+name+'.stderr')).write_text(err)
