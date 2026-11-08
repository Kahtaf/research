from pathlib import Path
import mmap,json,re,datetime
T=Path('/srv/android/lineage24');R=Path('/srv/android/asus-genuine-service-runtime')
needles=[b'out/soong/.intermediates/build/soong/system-build.prop/android_common/build.prop',b'out/soong/.intermediates/build/soong/system_ext-build.prop/android_common/build.prop',b'out/soong/.intermediates/build/soong/product-build.prop/android_common/build.prop',b'out/soong/.intermediates/bionic/apex/com.android.runtime/android_common_hwasan_com.android.runtime/com.android.runtime.apex',b'out/target/product/p00a/obj/PACKAGING/apexkeys_intermediates/apexkeys.txt',b'out/target/product/p00a/system/build.prop',b'out/target/product/p00a/system/etc/security/apexkeys.txt']
rows=[];seen=set()
for f in list((T/'out/soong').glob('build.lineage_p00a.*.ninja'))+list((T/'out').glob('build-lineage_p00a*.ninja')):
 with f.open('rb') as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ) as m:
  for needle in needles:
   pos=0
   while True:
    at=m.find(needle,pos)
    if at<0:break
    pos=at+len(needle)
    start=m.rfind(b'\nbuild ',0,at)
    if start<0:continue
    start+=1
    end=m.find(b'\n',start)
    while m[end-1:end]==b'$':end=m.find(b'\n',end+1)
    if at>end:continue
    edge=m[start:end].replace(b'$\n',b'').decode();outs=edge.split(': ',1)[0]
    if needle.decode() not in outs:continue
    key=(str(f),start)
    if key in seen:continue
    seen.add(key);parts=edge.split(': ',1);tokens=parts[1].split();inputs=[x for x in tokens[1:] if x not in ['|','||'] and not x.endswith('-deps')]
    # A build's indented variables include its genuine generator command/rsp.
    varend=m.find(b'\nbuild ',end)
    if varend<0:varend=end
    variables=m[end:min(varend,end+100000)].decode(errors='replace')
    rows.append(dict(ninja=str(f),edge=edge,variables=variables,inputs=[dict(path=x,exists=(T/x).exists()) for x in inputs]))
(R/'evidence/metadata-target-edges.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),edges=rows),indent=2))
for r in rows:print(r['edge'][:500], '\nmissing:',*[x['path'] for x in r['inputs'] if not x['exists']],sep='\n')
