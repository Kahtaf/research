"""Bounded-memory geometry scan over owned read-only frozen graph copies."""
import hashlib,json,os,resource,sys,time
from pathlib import Path
ROOT=Path('/srv/android/asus-official-runtime-capture/preparation-v4')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(120,120))
sys.path.insert(0,str(ROOT/'source'))
from safeio import Tree,need,write_json
start=time.monotonic();tree=Tree(ROOT/'graph-fixture/frozen');rows=[]
for path in ['out/build-lineage_p00a.ninja','out/soong/build.lineage_p00a.ninja','out/combined-lineage_p00a.ninja']:
    pin=tree.digest(path,2*1024**3)
    lines=0;maxline=0;maxblock=0;block=0;block_start=0;maxstart=0;continuation=False
    with tree.open(path) as f:
        while True:
            chunk=f.readline(65536)
            if not chunk:break
            first=chunk[:1];size=len(chunk);last=chunk
            while not last.endswith(b'\n'):
                last=f.readline(65536)
                if not last:break
                size+=len(last)
                need(size<=128*1024**2,'SCAN_LINE','finite exploratory 128 MiB line budget')
            lines+=1
            if block and not continuation and first not in (b' ',b'\t'):
                if block>maxblock:maxblock=block;maxstart=block_start
                block=0
            if not block:block_start=lines
            block+=size
            need(block<=128*1024**2,'SCAN_BLOCK','finite exploratory 128 MiB block budget')
            continuation=(last or chunk).rstrip(b'\n').endswith(b'$')
            maxline=max(maxline,size)
        if block>maxblock:maxblock=block;maxstart=block_start
    need(pin==tree.digest(path,2*1024**3),'DRIFT',path)
    rows.append({'path':path,'pin':pin,'lines':lines,'max_line_bytes':maxline,'max_block_bytes':maxblock,'max_block_start_line':maxstart})
tree.close()
u=resource.getrusage(resource.RUSAGE_SELF)
r={'schema':1,'scope':'frozen-graph-geometry-only','graphs':rows,'elapsed_seconds':round(time.monotonic()-start,3),'cpu_seconds':round(u.ru_utime+u.ru_stime,3),'max_rss_KiB':u.ru_maxrss,'address_space_limit_bytes':1024**3,'cpu_count':len(os.sched_getaffinity(0)),'cpu_seconds_limit':120,'scan_chunk_bytes':65536,'exploratory_line_block_ceiling_bytes':128*1024**2,'failed_fixture_preserved':True}
write_json(ROOT/'graph-fixture/block-geometry.json',r);print(json.dumps(r,indent=2))
