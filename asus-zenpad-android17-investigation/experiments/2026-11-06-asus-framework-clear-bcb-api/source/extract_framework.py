"""Selected public stock SYSTEM paths only. No whole-image hash/copy or device I/O."""
from pathlib import Path
import sys,struct,json,hashlib
S=Path(__file__).resolve().parents[1];W=S.parent
sys.path.insert(0,str(W/'2026-11-06-asus-stock-userdata-recovery/source'))
from ext4_reference import Ext4
P=W/'2026-11-06-asus-local-stock-rollback/artifacts/stock-rollback/system.img'
READY=W/'2026-11-06-asus-local-stock-rollback/artifacts/stock-rollback/READY.json'
assert P.stat().st_size==3753902080 and P.is_file() and not P.is_symlink()
r=json.loads(READY.read_text());assert r['status']=='LOCAL_SELECTED_STOCK_BYTES_VERIFIED' and r['files']['system.img']['sha256']=='4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49'
r.pop('hardware_serial',None);r['receipt_source']=str(READY);r['whole_image_rehashed_here']=False
(S/'evidence/system-READY.json').write_text(json.dumps(r,indent=2)+'\n')
e=Ext4(P);records=[]
paths=['framework/framework.jar','framework/services.jar','framework/arm64/boot-framework.oat','framework/oat/arm64/services.odex']
for path in paths:
 i=e.inode(e.lookup(path));mode=struct.unpack_from('<H',i,0)[0];size=struct.unpack_from('<I',i,4)[0]+(struct.unpack_from('<I',i,108)[0]<<32)
 assert mode&0xf000==0x8000 and size<64*1024*1024
 out=S/'inputs'/path.replace('/','__');digest=hashlib.sha256();ranges=[]
 with out.open('wb') as dest:
  position=0
  for logical,length,physical in sorted(e.extents(i[40:100])):
   start=logical*e.bs;count=min(length*e.bs,size-start);assert start==position and count>=0
   ranges.append({'image_offset':physical*e.bs,'length':count,'file_offset':start})
   for delta in range(0,count,1024*1024):
    piece=e.read(physical*e.bs+delta,min(1024*1024,count-delta));dest.write(piece);digest.update(piece)
   position+=count
  assert position==size
 records.append({'file':str(out.relative_to(S)),'system_path':'/system/'+path,'bytes':size,'sha256':digest.hexdigest(),'image_ranges':ranges})
e.f.close()
(S/'evidence/extraction.json').write_text(json.dumps({'source':str(P),'source_sha256_from_verified_receipt':r['files']['system.img']['sha256'],'whole_image_rehashed_or_copied':False,'files':records},indent=2)+'\n')
print(json.dumps([{k:v for k,v in x.items() if k!='image_ranges'} for x in records],indent=2))
