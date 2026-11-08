"""Small host format discriminators; no target execution or image output."""
import pathlib,json,zlib,resource,hashlib,struct
resource.setrlimit(resource.RLIMIT_CPU,(10,10))
R=pathlib.Path(__file__).resolve().parents[1];W=R.parent
src=W/'2026-11-06-asus-stock-only-ram-rescue-build/artifacts/candidate/UNAPPROVED-STOCK-ONLY.img'
b=src.read_bytes();assert hashlib.sha256(b).hexdigest()=='5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f'
ks,ka,rs,ra=struct.unpack_from('<4I',b,8);ro=2048+(ks+2047)//2048*2048
payload=b[ro+512:ro+rs];assert len(payload)==2935556
results=[]
for name,value in [('full-payload',payload),('hypothetical-static-DT-2MiB-bound',payload[:0x200000])]:
 d=zlib.decompressobj(31);raw=d.decompress(value,32*1024**2)
 results.append(dict(test=name,input_bytes=len(value),gzip_eof=d.eof,expanded_bytes=len(raw),consumed_bytes=len(value)-len(d.unused_data),hardware_execution=False))
assert results[0]['gzip_eof'] and not results[1]['gzip_eof']
assert results[0]['consumed_bytes']==2159874
assert payload[2159874:2159876]==b'\0\0' and 2159876%4==0
assert payload[2159876:2159882]==b'070701'
assert ra+rs<0x44400000
results.append(dict(test='fixed-ram-console-reservation',candidate_end=hex(ra+rs),reservation_start='0x44400000',gap_bytes=0x44400000-ra-rs,overlap=False,runtime_allocation_verified=False))
(R/'evidence/format-boundaries.json').write_text(json.dumps(results,indent=2)+'\n')
print('Full payload completes gzip; hypothetical 2MiB bound truncates it; aligned raw member and fixed range checks pass.')
