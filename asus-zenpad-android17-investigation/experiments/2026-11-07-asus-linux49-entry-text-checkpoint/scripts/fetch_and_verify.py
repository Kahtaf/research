from pathlib import Path
import sys,json,base64
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parent/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run
payload=(R/'scripts/verify_remote.py').read_text()
result=run('''from pathlib import Path
import subprocess
R=Path('/srv/android/asus-linux49-entry-text-checkpoint-20261107')
assert (R/'scripts/verify_remote.attempt2.py').exists() and not (R/'scripts/verify_remote.attempt3.py').exists()
(R/'scripts/verify_remote.py').rename(R/'scripts/verify_remote.attempt3.py')
(R/'scripts/verify_remote.py').write_text(PAYLOAD)
p=subprocess.run(['python3','-B',str(R/'scripts/verify_remote.py')],text=True,capture_output=True)
(R/'evidence/linked-verification.stdout').write_text(p.stdout)
(R/'evidence/linked-verification.stderr').write_text(p.stderr)
print(p.stdout);print(p.stderr)
if p.returncode: raise RuntimeError('Linked verification failed: '+p.stderr)
'''.replace('PAYLOAD',repr(payload)))
(R/'evidence/linked-verification-output.txt').write_text(result)
files={'artifacts/Image.gz-dtb':'out/arch/arm64/boot/Image.gz-dtb','artifacts/resolved.config':'out/.config'}
for n in ['source-copy.json','build-status.json','build-receipt.json','linked-entry.json','compiled-initcalls.json','entry.disasm']:
 files['evidence/'+n]='evidence/'+n
response=run('''from pathlib import Path
import json,base64,hashlib
R=Path('/srv/android/asus-linux49-entry-text-checkpoint-20261107')
files=FILES
d={n:dict(base64=base64.b64encode((R/p).read_bytes()).decode(),sha256=hashlib.sha256((R/p).read_bytes()).hexdigest()) for n,p in files.items()}
log=R/'evidence/Image.gz-dtb.log';d['evidence/build-log-summary.json']=dict(text=json.dumps(dict(bytes=log.stat().st_size,sha256=hashlib.sha256(log.read_bytes()).hexdigest(),tail=log.read_text(errors='replace').splitlines()[-25:]),indent=2)+'\\n')
print(json.dumps(d))
'''.replace('FILES',repr(files)))
import hashlib
summary={}
for n,v in json.loads(response).items():
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True)
 if 'base64' in v:
  data=base64.b64decode(v['base64']);assert hashlib.sha256(data).hexdigest()==v['sha256'];p.write_bytes(data);summary[n]=dict(bytes=len(data),sha256=v['sha256'])
 else:p.write_text(v['text'])
(R/'evidence/fetch-receipt.json').write_text(json.dumps(dict(fetched=summary,compact_only=True,vmlinux_fetched=False,full_tree_fetched=False,SSH='exact existing product-input-build-kit/scripts/remote.py'),indent=2)+'\n')
print(json.dumps(summary,indent=2))
