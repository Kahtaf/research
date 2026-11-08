from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parents[1];prior=json.loads((R/'evidence/closure-constructors.json').read_text())
remote='''from pathlib import Path
import subprocess,resource,os,hashlib,json,re
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-selected-camera-metadata');rows=PRIOR;added=[];total=0
img='/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img'
def inspect(path):
 global total
 data=subprocess.run(['debugfs','-R','cat '+path,img],capture_output=True,check=True,timeout=20).stdout
 if not data.startswith(b'\\x7fELF'):return None
 assert len(data)<40*1024**2
 total+=len(data);assert total<160*1024**2
 tmp=r/'closure-leaf.so';tmp.write_bytes(data)
 elf=subprocess.run(['readelf','--dyn-syms','-dW',str(tmp)],capture_output=True,text=True,check=True,timeout=20).stdout;tmp.unlink()
 return {'path':path,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'elfclass':data[4],'metadata_exports':[l.split()[-1] for l in elf.splitlines() if 'constructCust' in l and ' UND ' not in l],'needed':re.findall(r'Shared library: \\[(.*?)\\]',elf)}
srv=inspect('/bin/cameraserver');rows.append(srv);added.append(srv)
missing=[]
for w in ['lib','lib64']:
 current=[x for x in rows if ('/'+w+'/' in x['path'] or (w=='lib' and x['path']=='/bin/cameraserver')) and not x.get('absent')];have={x['path'].split('/')[-1] for x in current};queue=[n for x in current for n in x.get('needed',[])];attempt=set()
 while queue:
  n=queue.pop(0)
  if n in have or n in attempt:continue
  attempt.add(n);row=None
  for prefix in ['/vendor/'+w+'/', '/'+w+'/']:
   row=inspect(prefix+n)
   if row:break
  if row:
   assert row['elfclass']==(1 if w=='lib' else 2);rows.append(row);added.append(row);have.add(n);queue.extend(row['needed'])
  else:missing.append(w+'/'+n)
print(json.dumps({'scope':'Transitive stock DT_NEEDED closure of both prior camera factory seeds, stock core-provider leaves, plus actual 32-bit cameraserver; excludes unknown runtime injected/preloaded libraries','additional_bytes':total,'rows':rows,'additional_rows':len(added),'unresolved_needed':missing},indent=2))
'''.replace('PRIOR',repr(prior['rows']))
(R/'scripts/complete_closure_remote.py').write_text(remote)
ssh=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+str(Path.home()/'.ssh/google_compute_known_hosts'),'android@IP_REDACTED']
p=subprocess.run(ssh+['python3','-'],input=remote.encode(),capture_output=True,check=True);(R/'evidence/complete-closure-constructors.json').write_bytes(p.stdout);d=json.loads(p.stdout);print({k:v for k,v in d.items() if k!='rows'})
