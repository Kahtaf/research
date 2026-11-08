"""Use existing public libsepol sources read-only for a native host query tool.

This compiles an analysis tool only. It cannot build a target image or modify policy.
"""
import pathlib,subprocess,resource,json,hashlib,os
R=pathlib.Path(__file__).resolve().parents[1];W=R.parent
resource.setrlimit(resource.RLIMIT_CPU,(90,90))
limits={}
for kind in ('RLIMIT_AS','RLIMIT_DATA'):
 try:resource.setrlimit(getattr(resource,kind),(1024**3,resource.getrlimit(getattr(resource,kind))[1]));limits[kind]='1GiB'
 except ValueError as e:limits[kind]=str(e)
T=W/'2026-11-06-asus-android17-target-rescue/artifacts/tools-release/libsepol'
Q=W/'2026-11-06-asus-android17-target-rescue/source/policy_query.c'
dest=R/'evidence/native-policy-tool';dest.mkdir(exist_ok=True)
sources=['assertion','avtab','avrule_block','conditional','constraint','context','context_record','debug','ebitmap','expand','handle','hashtab','hierarchy','mls','polcaps','policydb','services','sidtab','symtab','util','write']
records=[];objs=[]
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
with (dest/'compile.log').open('w') as log:
 for name in sources:
  src=T/'src'/f'{name}.c';obj=dest/f'{name}.o'
  cmd=['/usr/bin/clang','-O0','-DDARWIN','-D_GNU_SOURCE','-Wno-deprecated-declarations','-I'+str(T/'include'),'-I'+str(T/'src'),'-c',str(src),'-o',str(obj)]
  records.append(dict(path=str(src),sha256=hashlib.sha256(src.read_bytes()).hexdigest(),argv=cmd))
  p=subprocess.run(cmd,stdout=log,stderr=log,env=env,timeout=20)
  if p.returncode:raise SystemExit('compile failed '+name)
  objs.append(str(obj))
 cmd=['/usr/bin/clang','-O0','-I'+str(T/'include'),str(Q),*objs,'-o',str(dest/'policy_query')]
 p=subprocess.run(cmd,stdout=log,stderr=log,timeout=20)
 if p.returncode:raise SystemExit('link failed')
records.append(dict(path=str(Q),sha256=hashlib.sha256(Q.read_bytes()).hexdigest(),argv=cmd))
(dest/'pins.json').write_text(json.dumps(dict(inputs=records,limits=limits,tool_sha256=hashlib.sha256((dest/'policy_query').read_bytes()).hexdigest()),indent=2)+'\n')
print('Native read-only policy query tool ready')
