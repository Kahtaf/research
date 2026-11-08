"""Full geometry production session control flow; symbolic hash/storage and frame boundaries.
No actual payload/GPT/recovery/source bytes read, no throughput prediction.
"""
from pathlib import Path
import json,os,resource,struct,subprocess,tempfile
R=Path(__file__).resolve().parents[1];C=1048576
sizes={9:16740352,10:16740352,25:3753902080,26:11331268096,0:15634268160}
starts={9:127488,10:160184,25:1072424,26:8404264}
h=lambda n:struct.pack('<Q',n)+bytes(24)
with tempfile.TemporaryDirectory(prefix='rsc-model-',dir='/tmp') as d:
 root=Path(d)
 def p(s):return root/s.lstrip('/')
 def write(s,b):q=p(s);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 manifest=b'ASUSR002'+struct.pack('<II',2,5)+h(32)+h(17408)+h(16896)
 for role,part in enumerate([25,9,25,9,26]):
  size=sizes[part];chunks=[h(min(C,size-o)) for o in range(0,size,C)]
  manifest+=struct.pack('<IIQ',role,part,size)+h(size)+struct.pack('<I',len(chunks))+b''.join(chunks)
 write('/rescue.manifest',manifest);write('/sys/fs/selinux/enforce',b'1');write('/sys/class/block/mmcblk0/device/cid',b'0'*32);write('/proc/self/mountinfo',b'1 0 0:1 / / rw - tmpfs tmpfs rw\n')
 for part,size in sizes.items():
  q=p('/dev/block/mmcblk0'+(f'p{part}' if part else ''));q.parent.mkdir(parents=True,exist_ok=True)
  with q.open('wb') as f:f.truncate(size)
  write(f'/sys/dev/block/179:{part}/dev',f'179:{part}'.encode());write(f'/sys/dev/block/179:{part}/size',str(size//512).encode())
  if part:write(f'/sys/dev/block/179:{part}/start',str(starts[part]).encode())
  p(f'/sys/dev/block/179:{part}/holders').mkdir()
 aliases=p('/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name');aliases.mkdir(parents=True)
 for part,name in [(9,'boot'),(10,'recovery'),(25,'system'),(26,'userdata')]: (aliases/name).symlink_to(p(f'/dev/block/mmcblk0p{part}'))
 p('/dev/rescue-state').mkdir()
 rows=[]
 for revision in ['before','after']:
  for role in [2,4,3]:
   for opcode in [7,4]:
    result=subprocess.run([str(R/f'tests/model-{revision}'),d,str(role),str(opcode==4 and 1 or 0)],text=True,capture_output=True,check=True)
    row=json.loads(result.stdout);row['revision']=revision;rows.append(row)
    count=row['chunks'];hashes=count+5 if revision=='before' else 5
    assert row['recovery_hashes']==hashes
    assert row['recovery_opens']==(hashes if revision=='before' else 1)
    assert row['recovery_read_calls']==hashes*16
    assert row['recovery_bytes']==hashes*16740352
 totals={rev:{k:sum(row[k] for row in rows if row['revision']==rev and row['opcode']==7) for k in ['chunks','recovery_opens','recovery_hashes','recovery_read_calls','recovery_bytes']} for rev in ['before','after']}
 assert totals['before']['recovery_bytes']-totals['after']['recovery_bytes']==241111289856
 print(json.dumps(dict(model_only=True,actual_recovery_payload_bytes_read=0,rows=rows,totals=totals,peak_child_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss),indent=2))
