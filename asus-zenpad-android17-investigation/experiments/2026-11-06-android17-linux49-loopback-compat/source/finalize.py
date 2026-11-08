#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,shutil,sys,subprocess
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
tools=[]
for name,path in [('python',sys.executable),('clang',shutil.which('clang'))]:
 p=Path(path).resolve();tools.append({'name':name,'path':str(p),'sha256':sha(p)})
(R/'evidence/tool-pins.json').write_text(json.dumps({'tools':tools,'python_version':sys.version,'remote_compiler':'Inherited clang-r584948b build command only; no active compiler binary read'},indent=2)+'\n')
for filename in ['frozen-selection.json','frozen-extra.json']:
 m=json.loads((R/'evidence'/filename).read_text())
 for f in m['files']:
  if not f.get('missing'):assert sha(R/'inputs/frozen'/f['path'])==f['sha256']
core=R/'inputs/frozen/handoff-r1/manifest.json'
assert sha(core)=='d6790e2efde8ddb11102f561b5c58129660be09d41f1bbfb66402f3865ef13dd'
assert sha(R/'inputs/frozen/handoff-r1/network.config')=='8323724c579329c40f33aa15531320e2fdefc7e8d190703d56a555eac890ba01'
log=(R/'inputs/frozen/run-r18/serial.log').read_text()
assert 'CROSS_PROFILE_RESULT failures=2' in log
failed=[l for l in log.splitlines() if l.startswith('CROSS_PROFILE_PACKET') and 'passed=0' in l]
assert len(failed)==2 and all('receiver_socket_uid=110002' in x and 'checks_enabled=1' in x and 'actual_delivery=1' in x for x in failed)
manifest={'status':'BLOCKED: runtime isolation failure remains; no kernel patch staged','new_remote_writes':False,'new_runtime_runs':0,'kernel_objects_built':0,'host_tests':json.loads((R/'evidence/host-tests.json').read_text())['status'],'baseline_failed_cases':failed,'files':[]}
for p in sorted(R.rglob('*')):
 if p.is_file() and p.name!='handoff-manifest.json':manifest['files'].append({'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p)})
(R/'evidence/handoff-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'files':len(manifest['files']),'bytes':sum(x['bytes'] for x in manifest['files']),'baseline_failures':len(failed),'status':manifest['status']}))
