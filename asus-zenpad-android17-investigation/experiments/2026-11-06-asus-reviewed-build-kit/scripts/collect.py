from remote import run
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
script='''from pathlib import Path
import hashlib,json,subprocess,os
R=Path('/srv/android/asus-build-continuation'); S=Path('/srv/android/asus-product-integration-staging/r1'); A=Path('/srv/android/lineage24'); P=Path('/srv/android/asus-device-product')
paths=[S/'STAGED.json']+[R/'integration-r5'/n for n in ['manifest.json','source-receipt.json','staged-product-receipt.json','network-applied.json','kernel.release']]+[R/'evidence'/n for n in ['snapshot.json','network-staging.json']]+[P/'scripts/build_full_product.sh',R/'inputs/google-inline-source-manifest.json']
result={}
for p in paths:
 if p.is_file():
  data=p.read_bytes();result[str(p)]={'sha256':hashlib.sha256(data).hexdigest(),'text':data.decode()}
result['kernel_link']={'target':str((A/'kernel/asus/p00a-fd').resolve())}
result['processes']=subprocess.check_output(['ps','-eo','pid,ppid,lstart,comm,args'],text=True).splitlines()
result['log_metadata']={p.name:{'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in (P/'logs').glob('full-build-r*')}
print(json.dumps(result))
'''
raw=json.loads(run(script))
# Avoid logging unrelated command arguments; only retain relevant build native names / original IDs.
raw['processes']=[l for l in raw['processes'] if any(x in l for x in ['78673','132874','soong_ui','soong_build',' ckati ',' siso ',' ninja '])]
(root/'evidence/remote-metadata.json').write_text(json.dumps(raw,indent=2)+'\n')
for path,item in raw.items():
 if isinstance(item,dict) and 'text' in item:
  name=Path(path).name
  if name=='manifest.json':name='handoff-manifest.json'
  (root/'inputs'/name).write_text(item['text'])
print('Collected metadata:',len(raw),'entries; active kernel',raw['kernel_link'])
