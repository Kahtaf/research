from pathlib import Path
import json,re,hashlib
A=Path('/srv/android/lineage24');R=Path('/srv/android/asus-reviewed-build-kit/r8/attempt/native-evidence/host_init_verifier')
requests=[(3,'bpfloader'),(7,'libvold'),(9,'vold')];o={'method':'Sorted module headers; bounded seeks, no graph index or whole-graph hash','modules':{},'auxiliary':{}}
for shard,module in requests:
 p=A/f'out/soong/build.lineage_p00a.{shard}.ninja';s=p.stat();needle=f'# Module:  {module}\n'.encode();lo=0;hi=s.st_size;reads=0
 with p.open('rb') as f:
  for _ in range(22):
   if hi-lo<4*1024*1024:break
   mid=(lo+hi)//2;f.seek(mid);b=f.read(min(4*1024*1024,s.st_size-mid));reads+=len(b);m=re.search(rb'# Module:  ([^\n]+)\n',b)
   if not m:raise ValueError('No next header in bounded window')
   name=m[1].decode();pos=mid+m.start()
   if name<module:lo=pos
   else:hi=mid
  f.seek(max(0,lo-1024));base=f.tell();b=f.read(min(12*1024*1024,s.st_size-base));reads+=len(b)
 matches=[m.start() for m in re.finditer(re.escape(needle),b)]
 assert matches,(module,lo,hi)
 start=matches[0];end=start
 # Include all adjacent variants of this exact module, stopping at next different module.
 for m in re.finditer(rb'# Module:  ([^\n]+)\n',b[start:]):
  if m[1].decode()!=module:end=start+m.start();break
 else:raise ValueError('module end outside bounded window')
 block=b[start:end];assert len(block)<6*1024*1024
 o['modules'][module]={'path':str(p.relative_to(A)),'offset':base+start,'bytes':len(block),'bytes_read':reads,'text':block.decode(),'before':{'bytes':s.st_size,'mtime_ns':s.st_mtime_ns},'after':{'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}}
for r in ['out/soong/.intermediates/system/bpf/loader/bpfloader/android_arm64_armv8-a/unstripped/bpfloader.clang.rsp','out/soong/.intermediates/system/vold/libvold/android_arm64_armv8-a_static/libvold.a.rsp']:
 p=A/r
 o['auxiliary'][r]={'text':p.read_text(),'bytes':p.stat().st_size} if p.is_file() and p.stat().st_size<1024*1024 else None
p=A/'out/soong/build.lineage_p00a.ninja'
o['main_prelude']=p.open('rb').read(110000).decode()
print(json.dumps(o,indent=2))
