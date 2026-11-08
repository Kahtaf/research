import os,resource,pathlib,json,hashlib,subprocess
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(120,120))
P=pathlib.Path;A=P('/srv/android/lineage24');R=P('/srv/android/asus-sdk37-system-ext4-qualification-20261106');d={'public_sources':{},'soong_stanzas':{}}
paths=[str(p) for p in (A/'external/e2fsprogs').rglob('*sparse*.c') if p.is_file()]
for s in paths:
 if 'sparse' in s and s.endswith('.c'):
  p=P(s);b=p.read_bytes();d['public_sources'][str(p)]={'sha256':hashlib.sha256(b).hexdigest(),'text':b.decode(errors='replace')}
p=A/'system/sepolicy/private/file_contexts';b=p.read_bytes();d['runas_context_source']={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'matches':[l for l in b.decode().splitlines()if 'run-as' in l]}
for p in (A/'out/soong').glob('build*.ninja'):
 stanzas=[]
 with p.open() as f:
  active=False
  for line in f:
   if line.startswith('build '):
    target=line.split(':',1)[0];active='/mkuserimg_mke2fs/' in target and target.endswith('/mkuserimg_mke2fs')
   if active:stanzas.append(line.rstrip())
 if stanzas:d['soong_stanzas'][str(p)]={'lines':stanzas,'sha256':hashlib.sha256(('\n'.join(stanzas)+'\n').encode()).hexdigest()}
(R/'final-sources.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
