from pathlib import Path
import urllib.request,json,hashlib,base64,concurrent.futures
R=Path(__file__).resolve().parents[1];U=R/'upstream';records=[]
def fetch(url,path,decode=False):
 with urllib.request.urlopen(url,timeout=25) as r:raw=r.read(1024*1024+1)
 assert len(raw)<=1024*1024
 path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
 b=base64.b64decode(raw) if decode else raw
 if decode:path.with_suffix(path.suffix+'.decoded').write_bytes(b)
 return {'url':url,'response_path':str(path.relative_to(R)),'response_sha256':hashlib.sha256(raw).hexdigest(),'decoded_sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)},b
def jget(repo,ref,path):
 z,b=fetch(f'https://android.googlesource.com/{repo}/+/{ref}?format=JSON',path);records.append(z);return json.loads(b[4:])
roots={}
for label,repo,ref in [('pie','kernel/configs','refs/heads/pie-release'),('s','kernel/configs','refs/heads/android12-platform-release'),('interfaces','platform/hardware/interfaces','f16c6d3a57')]:
 data=jget(repo,ref,U/label/'commit.json');roots[label]={'repo':repo,'commit':data['commit'],'tree':data['tree']}
requests=[]
for label in ['pie','s']:
 repo=roots[label]['repo'];commit=roots[label]['commit']
 for sub in (['p/android-4.9'] if label=='pie' else ['p/android-4.9','q/android-4.9']):
  tree=jget(repo,commit+'/'+sub+'/',U/label/sub/'tree.json')
  for entry in tree['entries']:
   if entry['type']=='blob':requests.append((repo,commit,sub+'/'+entry['name'],U/label/sub/entry['name']))
 if label=='s':
  for sub in ['README.md','Android.bp','build/kernel_config.go','tools/kconfig_xml_fixup.py']:
   requests.append((repo,commit,sub,U/label/sub))
for sub in ['compatibility_matrices/Android.bp','compatibility_matrices/compatibility_matrix.3.xml','compatibility_matrices/compatibility_matrix.4.xml','compatibility_matrices/build/compatibility_matrix.go']:
 requests.append((roots['interfaces']['repo'],roots['interfaces']['commit'],sub,U/'interfaces'/sub))
def job(t):
 repo,commit,sub,path=t
 try:
  z,b=fetch(f'https://android.googlesource.com/{repo}/+/{commit}/{sub}?format=TEXT',path,True)
  z.update({'repo':repo,'commit':commit,'source_path':sub,'git_blob_sha1':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()});return z
 except Exception as e:return {'repo':repo,'commit':commit,'source_path':sub,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:records+=list(pool.map(job,requests))
(R/'evidence/upstream-provenance.json').write_text(json.dumps({'roots':roots,'files':records},indent=2)+'\n')
print(json.dumps({'roots':roots,'files':len(records),'errors':[x for x in records if 'error'in x]},indent=2))
