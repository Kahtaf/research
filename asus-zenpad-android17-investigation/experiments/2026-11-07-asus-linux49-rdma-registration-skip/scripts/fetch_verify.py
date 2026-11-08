from pathlib import Path
import base64,hashlib,json,os,subprocess
from vm import R,channel
files={'scripts/verify_remote.py':(R/'scripts/verify_remote.py').read_bytes(),'source/identity.json':(R/'evidence/identity.json').read_bytes()}
script=r'''from pathlib import Path
import base64,hashlib,json,subprocess,gzip
R=Path('/srv/android/asus-linux49-rdma-registration-skip-20261107-d140b2bf')
for n,v in FILES.items():(R/n).write_bytes(base64.b64decode(v))
q=subprocess.run(['python3','-B',str(R/'scripts/verify_remote.py')],capture_output=True,text=True)
(R/'evidence/verify.stdout').write_text(q.stdout);(R/'evidence/verify.stderr').write_text(q.stderr)
if q.returncode==0:
 (R/'evidence/System.map.gz').write_bytes(gzip.compress((R/'out/System.map').read_bytes(),mtime=0))
fetch={'artifacts/System.map.gz':'evidence/System.map.gz','artifacts/Image.gz-dtb':'out/arch/arm64/boot/Image.gz-dtb','artifacts/resolved.config':'out/.config'} if q.returncode==0 else {}
for n in ['source-copy.json','source-pins.json','build-status.json','build-receipt.json','dispatch.json','verify.stdout','verify.stderr','linked-capture.json','capture-hooks.disasm','registration.disasm','compile-1.log']:
 if (R/'evidence'/n).exists():fetch['evidence/'+n]='evidence/'+n
print(json.dumps(dict(verify_exit=q.returncode,files={n:dict(data=base64.b64encode((R/p).read_bytes()).decode(),sha256=hashlib.sha256((R/p).read_bytes()).hexdigest()) for n,p in fetch.items()})))
'''.replace('FILES',repr({n:base64.b64encode(d).decode() for n,d in files.items()}))
os.chdir(R)
q=subprocess.run(channel()+['python3 -B -'],input=script,text=True,capture_output=True)
(R/'evidence/fetch.stderr').write_text(q.stderr);q.check_returncode();d=json.loads(q.stdout);receipt={}
for n,v in d['files'].items():
 data=base64.b64decode(v['data']);assert hashlib.sha256(data).hexdigest()==v['sha256'];(R/n).write_bytes(data);receipt[n]=dict(bytes=len(data),sha256=v['sha256'])
(R/'evidence/fetch-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(verify_exit=d['verify_exit'],artifacts={n:v for n,v in receipt.items() if n.startswith('artifacts/')}),indent=2))
if d['verify_exit']:print((R/'evidence/verify.stderr').read_text());raise SystemExit(d['verify_exit'])
