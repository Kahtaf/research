from pathlib import Path
import os,resource,signal,subprocess,json,time,hashlib,base64
R=Path('/srv/android/asus-stock-gpio28-review-20261106-r1');E=R/'evidence';K=R/'kernel'
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(90,90));signal.alarm(180);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
assert (E/'final-verification.json').exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for rel,h in json.loads((E/'candidate-source-manifest.json').read_text()).items():
 if rel.endswith('mt_soc_pcm_routing.c'):
  src=K/rel;assert sha(src)==h
  (E/'routing-PM-source-binding.json').write_text(json.dumps(dict(path=str(src),sha256=h,baseline_only=True,no_patch_read=True),indent=2)+'\n')
  (E/'routing-PM-caller.txt').write_text('\n'.join(src.read_text().splitlines()[1029:1113])+'\n')
def limit():resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_FSIZE,(128*1024**2,128*1024**2));os.setsid()
def run(cmd,name,expected):
 assert not (E/(name+'.json')).exists();start=time.time()
 with (E/(name+'.log')).open('wb') as f:
  p=subprocess.Popen([str(x) for x in cmd],cwd=R,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit)
  try:code=p.wait(timeout=45)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();code='WALL_TIMEOUT'
 row=dict(command=[str(x) for x in cmd],exit=code,expected_exit=expected,cpu_limit_seconds=30,wall_limit_seconds=45,wall_seconds=time.time()-start,rlimit_as=resource.getrlimit(resource.RLIMIT_AS),affinity=sorted(os.sched_getaffinity(0)))
 (E/(name+'.json')).write_text(json.dumps(row,indent=2)+'\n');print(name,code,flush=True)
 assert code==expected,(E/(name+'.log')).read_text()
for name,payload in PAYLOADS.items():
 src=R/'inputs/tests'/(name+'.c');src.write_bytes(base64.b64decode(payload));dest=R/'tmp'/name
 run(['gcc','-std=gnu89','-O0','-g','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-Wno-declaration-after-statement','-fsanitize=undefined','-fno-sanitize-recover=all',src,'-o',dest],name+'-compile',0)
 run([dest],name+'-run',1 if name=='lifetime-null' else 0)
 if name=='lifetime-null':assert 'runtime error: member access within null pointer' in (E/(name+'-run.log')).read_text()
print('BLOCKING_LIFETIME_REPRODUCED; no further ARM64/DTB compilation; no candidate fix')
