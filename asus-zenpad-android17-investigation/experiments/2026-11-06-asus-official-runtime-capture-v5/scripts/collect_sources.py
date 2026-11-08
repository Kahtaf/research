import hashlib,json,os,resource,sys,time
from pathlib import Path
ROOT=Path('/srv/android/asus-official-runtime-capture/preparation-v5');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(30,30));sys.path.insert(0,str(ROOT/'source'))
from safeio import Tree
start=time.monotonic();tree=Tree('/srv/android/lineage24');files={};total=0
names=['build/make/core/Makefile','build/make/core/definitions.mk','build/soong/apex/apex.go','build/soong/apex/builder.go','build/soong/apex/apex_keys.go','external/ninja/src/eval_env.cc','external/ninja/src/manifest_parser.cc','external/ninja/src/lexer.in.cc','external/ninja/src/graph.cc']
for name in names:
 try:data=tree.read(name,4*1024**2)
 except FileNotFoundError:files[name]={'missing':True};continue
 total+=len(data);assert total<=16*1024**2
 (ROOT/'evidence/public-source'/name).parent.mkdir(parents=True,exist_ok=True)
 with (ROOT/'evidence/public-source'/name).open('xb') as f:f.write(data)
 lines=data.decode().splitlines();matches=[]
 for i,line in enumerate(lines):
  if any(x in line for x in ('APEX_KEYS_FILE','apexkeys.txt','LookupVariable','val.Evaluate','simple_varname','LookupWithFallback')):
   matches.append({'line':i+1,'text':'\n'.join(lines[max(0,i-2):min(len(lines),i+4)])})
 files[name]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'matches':matches[:40]}
tree.close();r={'schema':1,'files':files,'bytes':total,'cpu_count':1,'address_space_limit_bytes':1024**3,'cpu_seconds_limit':30,'elapsed_seconds':round(time.monotonic()-start,3),'max_rss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
with (ROOT/'evidence/public-sources.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r))
