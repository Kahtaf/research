from pathlib import Path
import os,json,subprocess as s,shlex,hashlib,resource,shutil
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');S=R/'inputs/native-snapshot';W=R/'work/native';E=R/'evidence';os.environ['TMPDIR']=str(R/'tmp');os.environ['LD_LIBRARY_PATH']=str(S/'out/host/linux-x86/lib64');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0));P=json.loads((E/'native-snapshot-pins.json').read_text());data=json.loads((E/'actual-metadata.json').read_text());root=R/'inputs/actual-root';root.mkdir(exist_ok=True);(root/'system').mkdir(exist_ok=True);(root/'system/etc').mkdir(exist_ok=True);(root/'system/system_ext').mkdir(exist_ok=True);(root/'system/product').mkdir(exist_ok=True);(root/'system/vendor').mkdir(exist_ok=True);
for name,target in [('product','system/product'),('system_ext','system/system_ext'),('vendor','system/vendor')]:
 if not (root/name).is_symlink():(root/name).symlink_to(target)
for path,row in data['filesystem_files'].items():
 if row.get('exists') is False:continue
 src=R/'inputs/actual'/path;dst=root/path;dst.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(src,dst)
# Typed input records exactly match all actual package manifest/configuration metadata.
cpp=['#include "linkerconfig/apex.h"\n#include <vector>\nusing android::linkerconfig::modules::ApexInfo;\nstd::vector<ApexInfo> ActualApexRecords(bool bootstrap) { std::vector<ApexInfo> out;\n']
q=lambda x:json.dumps(x);vec=lambda x:'{'+','.join(q(v) for v in x)+'}'
bootstrap={'com.android.i18n','com.android.runtime','com.android.virt','com.android.tzdata'}
for row in sorted(data['packages'],key=lambda x:x['name']):
 code='ApexInfo a('+','.join([q(row['name']),q(row['path']),vec(row['provide_libs']),vec(row['require_libs']),vec(row['jni_libs']),vec(row['permitted_paths'])]+[str(row[k]).lower() for k in ['has_bin','has_lib','visible','has_shared_lib']])+');a.partition='+q(row['partition'])+';a.public_libs='+vec(row['public_libs'])+';out.push_back(std::move(a));'
 cpp.append(('if(!bootstrap)' if row['name'] not in bootstrap else '')+'{'+code+'}\n')
cpp.append('return out;}\n');(W/'actual_records.h').write_text(''.join(cpp));(W/'generate_actual.cc').write_bytes((R/'source/generate_actual.cc').read_bytes());edges=P['selected_edges']['host'];flags=shlex.split(edges['testcc']['expanded']['cFlags'])+['-I'+str(W),'-Isystem/linkerconfig/generator/include'];T=P['tools'];commands=json.loads((E/'actual-generator-commands.json').read_text()) if (E/'actual-generator-commands.json').exists() else []
def run(cmd,check=True):
 p=s.run([str(x) for x in cmd],cwd=S,capture_output=True,text=True,timeout=90);commands.append(dict(command=[str(x) for x in cmd],rc=p.returncode,stdout=p.stdout,stderr=p.stderr));(E/'actual-generator-commands.json').write_text(json.dumps(commands,indent=2));
 if check:assert p.returncode==0,p.stderr
 return p
obj=W/'generate_actual.o';run([T['clang++']['path'],'-c']+flags+['-o',obj,W/'generate_actual.cc'])
for name,fixed in [('before',False),('after',True)]:
 ld=edges['ld'];v=ld['expanded'];rsp=' '.join([str(obj) if x.endswith('/main.o') else x for x in ld['inputs']])+' '+v['libFlags']
 if fixed:rsp=rsp.replace(edges['ar']['out'][0],str(W/'host-linkerconfig_contents.a'))
 response=W/('actual-'+name+'.rsp');response.write_text(rsp);exe=W/('actual-'+name);run([T['clang++']['path']]+shlex.split(v.get('crtBegin',''))+['@'+str(response)]+shlex.split(v.get('crtEnd',''))+['-o',exe]+shlex.split(v['ldFlags'])+shlex.split(v.get('extraLibFlags','')))
 for mode in ['bootstrap','full']:
  out=R/'work'/('actual-'+name+'-'+mode+'.ld.config.txt');p=run([exe,root,mode,out],check=False);(E/('generator-'+name+'-'+mode+'.log')).write_text(p.stdout+p.stderr)
  if not fixed:assert p.returncode==-6 and 'duplicate: heapprofd_client_api.so is provided by default and system in [vendor]' in p.stderr,p.stderr
  else:assert p.returncode==0,p.stderr
summary={'before_bootstrap_and_full':'SIGABRT exact actual duplicate-provider error','after_bootstrap_and_full':'exit0 genuine CreateBaseConfiguration and per-APEX configuration generation','bootstrap_apex_records':4,'full_apex_records':len(data['packages']),'system_provide_records':None,'harness_scope':'Only actual metadata loading and file-output driver; original Context, all contents/namespace/section/configuration builders, resolver, duplicate/missing guards and writer are genuine selected native objects. No APEX activation/trust claim.'}
import re
log=(E/'generator-after-full.log').read_text();m=re.search(r'record_count=(\d+)',log);summary['system_provide_records']=int(m[1]);(E/'actual-generation-result.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
