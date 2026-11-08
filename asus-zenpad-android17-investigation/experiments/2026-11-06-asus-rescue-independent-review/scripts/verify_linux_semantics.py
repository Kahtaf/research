"""Sequential bounded production reproduction and compiled-context queries in own fixture."""
import hashlib,json,shlex,subprocess
from pathlib import Path
from run_linux_review import R,S,REMOTE,SSH
F=R.parent/'2026-11-06-asus-rescue-block-context-fix'
files={'source/proxy.c':(S/'source/proxy.c').read_bytes(),'kind-contexts.txt':(F/'artifacts/file_contexts').read_bytes()}
pins={n:hashlib.sha256((S/'artifacts/tools-delivery'/n).read_bytes()).hexdigest() for n in ('context_lookup','policy_constraints','sefcontext_compile')}
payload={'files':{k:v.hex() for k,v in files.items()},'pins':pins,'root':REMOTE}
code='''
import os,resource,hashlib,json,subprocess,pathlib,sys
R=pathlib.Path(payload['root']);os.chdir(R)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(90,90))
for name,h in payload['files'].items():
 with (R/name).open('xb') as f:f.write(bytes.fromhex(h))
T=pathlib.Path('/srv/android/asus-target-rescue/artifacts/tools-delivery');sha=lambda b:hashlib.sha256(b).hexdigest()
for n,h in payload['pins'].items():assert sha((T/n).read_bytes())==h
E=R/'evidence/semantics';E.mkdir();commands=[]
def run(cmd,rc=0):
 p=subprocess.run([str(x) for x in cmd],capture_output=True,text=True,timeout=20)
 commands.append(dict(command=[str(x) for x in cmd],returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 (E/'commands.json').write_text(json.dumps(commands,indent=2))
 assert p.returncode==rc,(cmd,p.stderr,p.stdout)
 return p.stdout.strip()
for name,src,want in [('os-rescue','rescue.c','30ae9252e575d7c9c837783d60e51016a16bcadb46bd38215d8e49e5bb5d1c53'),('rescue-proxy','proxy.c','f915eca1b2ae5250afef76d3154a853b933278c283f82cfb4eb0cee7d2736d0f')]:
 run(['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-misleading-indentation','-Wl,--build-id=none',R/'source'/src,'-o',R/'artifacts'/name])
 assert sha((R/'artifacts'/name).read_bytes())==want,name
run([T/'sefcontext_compile',R/'kind-contexts.txt'])
C=R/'kind-contexts.txt.bin';assert sha(C.read_bytes())=='7723428608524a84b06144e4d48836c65219fe48503f230070567063b50b3f89'
lookups=[]
for part,alias,typ in [(9,'boot','boot'),(10,'recovery','recovery'),(25,'system','system'),(26,'userdata','userdata'),(0,None,'disk')]:
 node='/dev/block/mmcblk0'+(str('p'+str(part)) if part else '')
 paths=[node]+(['/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/'+alias] if alias else [])
 for path in paths:
  for mode in ['060600','120777','100600']:
   want='u:object_r:rescue_'+typ+'_device:s0' if mode=='060600' else 'u:object_r:block_device:s0'
   got=run([T/'context_lookup',C,path,mode]);assert got==want,(path,mode,got)
   lookups.append(dict(path=path,mode=mode,expected=want))
 if alias:
  got=run([T/'context_lookup',C,node,'060600',paths[1]]);assert got=='u:object_r:rescue_'+typ+'_device:s0'
  lookups.append(dict(path=node,alias=paths[1],mode='060600',expected=got))
P=R/'artifacts/candidate-delivery/rescue-sepolicy';assert sha(P.read_bytes())=='189c477ac73ecb161a6527f7f98a6fec76a913b0d5cf8d11591d440dc79af842'
policies=[]
for domain,typ,kind,perms,rc in [('os_rescue','block_device','lnk_file','read,getattr',0),('ueventd','block_device','lnk_file','create,getattr,unlink',0),('init','block_device','lnk_file','read,getattr',0),('os_rescue','rescue_recovery_device','blk_file','write',1),('os_rescue','rescue_disk_device','blk_file','write',1),('os_rescue','rescue_userdata_device','blk_file','open,read,write',1)]:
 got=run([T/'policy_constraints',P,'u:r:'+domain+':s0','u:object_r:'+typ+':s0',kind,perms],rc)
 assert ('allowed=1' if rc==0 else 'allowed=0') in got
 policies.append(dict(domain=domain,type=typ,kind=kind,permissions=perms,allowed=rc==0))
report=dict(passed=True,production_binaries_byte_identical=['os-rescue','rescue-proxy'],context_queries=lookups,policy_queries=policies,compiled_context_sha256=sha(C.read_bytes()),cpu_affinity=sorted(os.sched_getaffinity(0)),address_space_limit=resource.getrlimit(resource.RLIMIT_AS),physical_label_assignment_proved=False)
(E/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
'''
program='payload='+repr(payload)+'\n'+code
(R/'scripts/remote_semantics.py').write_text(program)
p=subprocess.run(SSH+['python3 -B -'],input=program,text=True,capture_output=True,timeout=100)
(R/'evidence/semantics.stdout').write_text(p.stdout);(R/'evidence/semantics.stderr').write_text(p.stderr)
if p.returncode:raise RuntimeError('semantics failed; preserve fixture and evidence')
report=json.loads(p.stdout);(R/'evidence/linux-semantics.json').write_text(json.dumps(report,indent=2)+'\n')
q=subprocess.run(SSH+['cat '+shlex.quote(REMOTE+'/evidence/semantics/commands.json')],capture_output=True,timeout=20,check=True)
(R/'evidence/linux-semantics-commands.json').write_bytes(q.stdout)
print(json.dumps(dict(passed=True,context_queries=len(report['context_queries']),policy_queries=len(report['policy_queries']),production_binaries_byte_identical=report['production_binaries_byte_identical'])))
