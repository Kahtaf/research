from pathlib import Path
import os,json,subprocess as sp,hashlib,shlex,resource
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');S=R/'inputs/native-snapshot';W=R/'work/native';W.mkdir(exist_ok=True);os.environ['TMPDIR']=str(R/'tmp');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0));p=json.loads((R/'evidence/native-snapshot-pins.json').read_text());T=p['tools'];commands=[]
def run(cmd,cwd=S,timeout=90,env=None):
 q=sp.run([str(x) for x in cmd],cwd=cwd,capture_output=True,text=True,timeout=timeout,env=env);commands.append(dict(command=[str(x) for x in cmd],cwd=str(cwd),rc=q.returncode,stdout=q.stdout,stderr=q.stderr));(R/'evidence/native-build-commands.json').write_text(json.dumps(commands,indent=2));assert q.returncode==0,q.stderr;return q
source=S/'system/linkerconfig/contents/namespace/systemdefault.cc';original=source.read_text();needle='  ns.AddProvides(ctx.GetSystemProvideLibs());';replacement='''  // The legacy vendor default shares core search paths, but BuildVendorSection
  // also creates the system namespace, which owns the SYSTEM provider records.
  if (!(ctx.IsDefaultConfig() && ctx.IsVendorSection() &&
        modules::IsP00aLegacyGraphics())) {
    ns.AddProvides(ctx.GetSystemProvideLibs());
  }''';assert original.count(needle)==1;fixed=W/'systemdefault.cc';fixed.write_text(original.replace(needle,replacement));summary={}
# Pin all inputs before invoking any compiler. The snapshot itself remains unchanged.
for rel,row in p['files'].items():assert hashlib.sha256((S/rel).read_bytes()).hexdigest()==row['sha256'],rel
for key,edges in p['selected_edges'].items():
 if key=='arm64' and (W/'arm64-generator.stripped').is_file():
  summary[key]={'generator':{'path':str(W/'arm64-generator'),'bytes':(W/'arm64-generator').stat().st_size,'sha256':hashlib.sha256((W/'arm64-generator').read_bytes()).hexdigest(),'stripped':{'path':str(W/'arm64-generator.stripped'),'bytes':(W/'arm64-generator.stripped').stat().st_size,'sha256':hashlib.sha256((W/'arm64-generator.stripped').read_bytes()).hexdigest()}}};continue
 cc=edges['cc'];out=W/(key+'-systemdefault.o');flags=shlex.split(cc['expanded']['cFlags']);run([T['clang++']['path'],'-c']+flags+['-MD','-MF',str(out)+'.d','-o',out,fixed],timeout=60)
 ar=edges['ar'];archive=W/(key+'-linkerconfig_contents.a');inputs=[str(out) if x==cc['out'][0] else x for x in ar['inputs']];rsp=W/(key+'-archive.rsp');rsp.write_text(' '.join(shlex.quote(x) for x in inputs));run([T['llvm-ar']['path']]+shlex.split(ar['expanded']['arFlags'])+[archive,'@'+str(rsp)])
 result={}
 for name,ed in [('generator',edges['ld'])]+([('tests',edges['testld'])] if key=='host' else []):
  v=ed['expanded'];orig_rsp=' '.join(ed['inputs'])+' '+v['libFlags'];orig_rsp=orig_rsp.replace(ar['out'][0],str(archive));extra=[]
  if name=='tests':
   test=W/'namespace_ownership_test.cc';test.write_bytes((R/'source/namespace_ownership_test.cc').read_bytes());tc=edges['testcc'];tf=shlex.split(tc['expanded']['cFlags']);testobj=W/'namespace_ownership_test.o';run([T['clang++']['path'],'-c']+tf+['-MD','-MF',str(testobj)+'.d','-o',testobj,test],timeout=60);orig_rsp+=' '+str(testobj)
  rsp=W/(key+'-'+name+'.rsp');rsp.write_text(orig_rsp);binary=W/(key+'-'+name);lf=shlex.split(v['ldFlags']);lf=[x.replace('out/soong/.thinlto-cache',str(R/'tmp'/('thinlto-'+key))) for x in lf];lf=[re.sub(r'--thinlto-jobs=\d+','--thinlto-jobs=1',x) for x in lf] if False else lf
  # Affinity enforces one CPU; restrict ThinLTO worker count explicitly as well.
  import re
  lf=[re.sub(r'--thinlto-jobs=\d+','--thinlto-jobs=1',x) for x in lf]
  run([T['clang++']['path']]+shlex.split(v.get('crtBegin',''))+['@'+str(rsp)]+shlex.split(v.get('crtEnd',''))+['-o',binary]+lf+shlex.split(v.get('extraLibFlags','')),timeout=90)
  result[name]={'path':str(binary),'bytes':binary.stat().st_size,'sha256':hashlib.sha256(binary.read_bytes()).hexdigest()}
  if key=='arm64':
   stripped=W/'arm64-generator.stripped';run([T['llvm-strip']['path'],'--strip-all','-o',stripped,binary]);result[name]['stripped']={'path':str(stripped),'bytes':stripped.stat().st_size,'sha256':hashlib.sha256(stripped.read_bytes()).hexdigest()}
 summary[key]=result
for rel,row in p['files'].items():assert hashlib.sha256((S/rel).read_bytes()).hexdigest()==row['sha256'],rel
for n,row in T.items():assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256']
(R/'evidence/native-candidates.json').write_text(json.dumps(dict(outputs=summary,snapshot_unchanged=True,tools_unchanged=True,changed_product_source='contents/namespace/systemdefault.cc',resource_adaptations=['one-CPU affinity','4GiB AS','ThinLTO jobs=1','owned cache/TMPDIR','own output/rsp paths'],new_test_only='contents/tests/configuration/namespace_ownership_test.cc'),indent=2));print(json.dumps(summary,indent=2))
