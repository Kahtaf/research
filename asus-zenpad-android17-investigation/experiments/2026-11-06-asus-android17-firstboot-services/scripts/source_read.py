#!/usr/bin/env python3
"""Capture named Android source files via read-only SSH; never invoke a build."""
import hashlib, json, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
SSH = ['ssh', '-i', str(pathlib.Path.home()/'.ssh/asus_p00a_android17'), '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'StrictHostKeyChecking=yes', '-o', 'HostKeyAlias=compute.8549823276971553556', '-o', 'UserKnownHostsFile='+str(pathlib.Path.home()/'.ssh/google_compute_known_hosts'), 'android@IP_REDACTED']
paths = sys.argv[1:]
program = '''import pathlib,json,hashlib,subprocess
root=pathlib.Path('/srv/android/lineage24')
result={}
for name in NAMES:
 p=root/name
 if p.is_file():
  data=p.read_bytes()
  result[name]={'text':data.decode(), 'sha256':hashlib.sha256(data).hexdigest()}
 else: result[name]={'missing':True}
print(json.dumps(result))
'''.replace('NAMES',repr(paths))
result=json.loads(subprocess.check_output(SSH+['python3 -B -'],input=program.encode()))
for name,value in result.items():
 if 'text' in value:
  target=ROOT/'evidence/source'/name
  target.parent.mkdir(parents=True,exist_ok=True)
  target.write_text(value['text'])
 print(name, value.get('sha256','MISSING'))
manifest=ROOT/'evidence/source-sha256.json'
previous=json.loads(manifest.read_text()) if manifest.exists() else {}
previous.update({k:{a:b for a,b in v.items() if a!='text'} for k,v in result.items()})
manifest.write_text(json.dumps(previous,indent=2)+'\n')
