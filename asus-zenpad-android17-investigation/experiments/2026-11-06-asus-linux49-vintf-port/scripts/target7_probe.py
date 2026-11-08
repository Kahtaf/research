from pathlib import Path
import json,subprocess,hashlib,shutil,time
P=Path('/srv/android/asus-linux49-vintf-port-20261106');B=P/'baseline';D=P/'diagnostic-target7'
shutil.copytree(B,D)
m=D/'vendor/etc/vintf/manifest.xml';s=m.read_text();assert '<manifest version="9.0" type="device">' in s;m.write_text(s.replace('<manifest version="9.0" type="device">','<manifest version="9.0" type="device" target-level="7">',1))
r=json.loads((P/'checks/00-resolved-baseline.json').read_text());a=[x.replace(str(B),str(D)) for x in r['argv']]
t=time.monotonic();q=subprocess.run(a,capture_output=True,text=True,timeout=30)
log=P/'checks/01-explicit-target7.log';log.write_text(q.stdout+q.stderr)
z={'argv':a,'exit':q.returncode,'seconds':time.monotonic()-t,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'status':'REJECTED_DIAGNOSTIC_NOT_CANDIDATE','purpose':'Expose deprecation obligations if adopting oldest supplied FCM; does not assert device implements FCM7.'}
(P/'checks/01-explicit-target7.json').write_text(json.dumps(z,indent=2));print(json.dumps({'receipt':z,'log':log.read_text()}))
