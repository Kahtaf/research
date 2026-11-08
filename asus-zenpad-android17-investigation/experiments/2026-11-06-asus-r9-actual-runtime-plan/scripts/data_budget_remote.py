import os,pathlib,json,zipfile,resource,signal
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(90)
P=pathlib.Path;R=P('/srv/android/lineage24/out/target/product/p00a/system/apex');rows=[]
for p in sorted(R.glob('*.capex')):
 with zipfile.ZipFile(p)as z:
  matches=[i for i in z.infolist()if i.filename=='original_apex'];assert len(matches)==1
  rows.append(dict(path=str(p),container_bytes=p.stat().st_size,decompressed_apex_bytes=matches[0].file_size))
total=sum(x['decompressed_apex_bytes']for x in rows)
print(json.dumps(dict(capex_count=len(rows),decompressed_total_bytes=total,metadata_only_no_decompression=True,capex=rows),indent=2))
