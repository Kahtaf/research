"""Read genuine public init source only, never inspect installed output availability."""
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('parent_remote',ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
script=r'''import datetime,hashlib,json,os,resource
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
p=Path('/srv/android/lineage24/system/core/init/property_service.cpp')
if p.resolve()!=p:raise RuntimeError('source path not canonical')
with p.open('rb') as f:data=f.read(1024*1024+1)
if len(data)>1024*1024:raise RuntimeError('bounded public source exceeded')
lines=data.decode().splitlines()
start=next(i for i,line in enumerate(lines) if 'void PropertyLoadBootDefaults()' in line)
end=next(i for i in range(start,len(lines)) if 'initialize_microdroid_properties(&properties)' in lines[i])
excerpt='\n'.join(lines[start:end])+'\n'
for literal in ('/<part>/etc/build.prop is the canonical location','/system/build.prop','load_properties_from_partition("system_ext", /* support_legacy_path_until */ 30)','load_properties_from_partition("product", /* support_legacy_path_until */ 30)'):
 if literal not in excerpt:raise RuntimeError('public init premise changed: '+literal)
receipt={'schema':1,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(p),'source_sha256':hashlib.sha256(data).hexdigest(),'source_bytes':len(data),'start_line':start+1,'end_line':end,'excerpt':excerpt,'public_source_only':True,'installed_outputs_inspected':False,'cpu_count':len(os.sched_getaffinity(0)),'address_space_limit_bytes':resource.getrlimit(resource.RLIMIT_AS)[0]}
with Path('/srv/android/asus-official-runtime-capture/preparation-v3/evidence/public-init-premise.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
print(json.dumps(receipt))
'''
result=json.loads(remote.run(script))
with (ROOT/'evidence/public-init-premise.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='excerpt'}))
