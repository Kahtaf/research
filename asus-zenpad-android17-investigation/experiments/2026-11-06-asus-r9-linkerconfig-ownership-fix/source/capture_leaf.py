from pathlib import Path
import re,os,json,hashlib
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');A=Path('/srv/android/lineage24');os.environ['TMPDIR']=str(R/'tmp');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});D=R/'inputs/leaf';D.mkdir();heads=[]
for i in range(10):
 p=A/f'out/soong/build.lineage_p00a.{i}.ninja';b=p.open('rb').read(512*1024);m=re.search(rb'# Module:  ([^\n]+)',b);heads.append((i,m[1].decode() if m else None,p.stat().st_size))
print(json.dumps(heads));(R/'evidence/graph-shard-boundaries.json').write_text(json.dumps(heads,indent=2))
requests=['linkerconfig','linkerconfig_contents','linkerconfig_modules','linkerconfig_generator','linkerconfig_contents_fulltest'];results={}
for module in requests:
 candidates=[i for j,(i,name,size) in enumerate(heads) if name is not None and name<=module and (j==9 or heads[j+1][1] is None or module<heads[j+1][1])];assert len(candidates)==1,(module,candidates,heads);i=candidates[0];p=A/f'out/soong/build.lineage_p00a.{i}.ninja';st=p.stat();lo=0;hi=st.st_size;reads=0
 with p.open('rb') as f:
  for _ in range(22):
   if hi-lo<1024*1024:break
   mid=(lo+hi)//2;f.seek(mid);b=f.read(min(2*1024*1024,st.st_size-mid));reads+=len(b);m=re.search(rb'# Module:  ([^\n]+)\n',b);assert m
   name=m[1].decode();pos=mid+m.start()
   if name<module:lo=pos
   else:hi=mid
  f.seek(max(0,lo-1024));base=f.tell();b=f.read(min(6*1024*1024,st.st_size-base));reads+=len(b)
 needle=('# Module:  '+module+'\n').encode();start=b.index(needle);end=None
 for m in re.finditer(rb'# Module:  ([^\n]+)\n',b[start:]):
  if m[1].decode()!=module:end=start+m.start();break
 assert end is not None
 block=b[start:end];(D/(module+'.ninja')).write_bytes(block);after=p.stat();assert (st.st_size,st.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
 results[module]=dict(shard=str(p),offset=base+start,bytes=len(block),sha256=hashlib.sha256(block).hexdigest(),bounded_bytes_read=reads,source_identity_unchanged=True)
p=A/'out/soong/build.lineage_p00a.ninja';b=p.open('rb').read(512*1024);(D/'main-prelude.ninja').write_bytes(b)
(R/'evidence/leaf-capture.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
