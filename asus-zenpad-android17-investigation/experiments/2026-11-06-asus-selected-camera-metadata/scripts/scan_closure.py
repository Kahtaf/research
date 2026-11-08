from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parents[1];W=R.parent
manifests=[W/'2026-11-06-asus-camera-arm32-route/evidence/extended-closure.json',W/'2026-11-06-asus-camera-source-abi-route/evidence/dependency-audit.json']
paths={}
for p in manifests:
 d=json.loads(p.read_text())
 for n,v in d['vendor_libraries'].items():paths[v['path']]=v['sha256']
 for n in d['modern_providers']:paths[('/lib/' if d['architecture']=='ARM32' else '/lib64/')+n]=None
# Exact SYSTEM binary inputs; generic system dependencies are inventory only.
payload=json.dumps(paths)
remote='''from pathlib import Path
import subprocess,resource,os,hashlib,json,re
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-selected-camera-metadata');r.mkdir(exist_ok=True);rows=[];total=0
paths=PAYLOAD
for path,prior in paths.items():
 data=subprocess.run(['debugfs','-R','cat '+path,'/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img'],capture_output=True,check=True,timeout=20).stdout
 if not data.startswith(b'\\x7fELF'):
  rows.append({'path':path,'absent':True});continue
 assert len(data)<24*1024**2
 total+=len(data);assert total<160*1024**2
 sha=hashlib.sha256(data).hexdigest()
 if prior:assert sha==prior,(path,sha,prior)
 tmp=r/'closure-leaf.so';tmp.write_bytes(data)
 elf=subprocess.run(['readelf','--dyn-syms','-dW',str(tmp)],capture_output=True,text=True,check=True,timeout=20).stdout
 exports=[l.split()[-1] for l in elf.splitlines() if 'constructCust' in l and ' UND ' not in l]
 rows.append({'path':path,'sha256':sha,'bytes':len(data),'prior_pin_matched':prior is not None,'metadata_exports':exports,'needed':re.findall(r'Shared library: \\[(.*?)\\]',elf)})
 tmp.unlink()
print(json.dumps({'scope':'Prior pinned camera DT_NEEDED closures + explicit factory seeds and stock core provider leaves; not an arbitrary preloaded runtime namespace','total_bytes':total,'rows':rows},indent=2))
'''.replace('PAYLOAD',repr(paths))
(R/'scripts/scan_closure_remote.py').write_text(remote)
ssh=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+str(Path.home()/'.ssh/google_compute_known_hosts'),'android@IP_REDACTED']
p=subprocess.run(ssh+['python3','-'],input=remote.encode(),capture_output=True,check=True);(R/'evidence/closure-constructors.json').write_bytes(p.stdout);d=json.loads(p.stdout)
print('leaves',len(d['rows']),'bytes',d['total_bytes']);print(json.dumps([x for x in d['rows'] if x.get('metadata_exports')],indent=2))
