from pathlib import Path
import base64,gzip,hashlib,json,os,subprocess
from vm import R,channel
i=json.loads((R/'evidence/identity.json').read_text())
files={'scripts/verify_remote.py':(R/'scripts/verify_remote.py').read_bytes()}
script='''from pathlib import Path
import base64,gzip,hashlib,json,subprocess
R=Path(ROOT)
for n,v in FILES.items():(R/n).write_bytes(base64.b64decode(v))
q=subprocess.run(['python3','-B',str(R/'scripts/verify_remote.py')],capture_output=True,text=True)
(R/'evidence/verify.stdout').write_text(q.stdout);(R/'evidence/verify.stderr').write_text(q.stderr)
if q.returncode==0:(R/'evidence/System.map.gz').write_bytes(gzip.compress((R/'out/System.map').read_bytes(),mtime=0))
fetch={'artifacts/System.map.gz':'evidence/System.map.gz','artifacts/Image.gz-dtb':'out/arch/arm64/boot/Image.gz-dtb','artifacts/resolved.config':'out/.config'} if q.returncode==0 else {}
for n in ['source-copy.json','source-pins.json','base-freeze.json','build-status.json','build-receipt.json','dispatch.json','verify.stdout','verify.stderr','source-checks.json','linked-capture.json','repository-preservation.json','compile-1.log','retained-recorder-object.disasm','retained-recorder-object.nm','scoped-linked.disasm','watchdog-object.disasm','watchdog-linked.json']:
 if (R/'evidence'/n).exists():fetch['evidence/'+n]='evidence/'+n
print(json.dumps(dict(verify_exit=q.returncode,files={n:dict(data=base64.b64encode((R/p).read_bytes()).decode(),sha256=hashlib.sha256((R/p).read_bytes()).hexdigest()) for n,p in fetch.items()})))
'''.replace('ROOT',repr(i['remote_root'])).replace('FILES',repr({n:base64.b64encode(v).decode() for n,v in files.items()}))
os.chdir(R)
q=subprocess.run(channel()+['python3 -B -'],input=script,text=True,capture_output=True)
(R/'evidence/fetch.stderr').write_text(q.stderr)
q.check_returncode();d=json.loads(q.stdout);receipt={}
for n,v in d['files'].items():
 data=base64.b64decode(v['data']);assert hashlib.sha256(data).hexdigest()==v['sha256']
 (R/n).write_bytes(data);receipt[n]=dict(bytes=len(data),sha256=v['sha256'])
(R/'evidence/fetch-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
if d['verify_exit']:
 print((R/'evidence/verify.stderr').read_text());raise SystemExit(d['verify_exit'])
mapdata=gzip.decompress((R/'artifacts/System.map.gz').read_bytes())
pin=dict(bytes=len(mapdata),sha256=hashlib.sha256(mapdata).hexdigest())
assert pin==json.loads((R/'evidence/build-receipt.json').read_text())['artifacts']['System.map']
(R/'artifacts/System.map').write_bytes(mapdata)
(R/'evidence/System.map-uncompressed.json').write_text(json.dumps(dict(status='PASS_GENUINE_VM_MAP',compressed_sha256=receipt['artifacts/System.map.gz']['sha256'],uncompressed=pin,vmlinux_fetched=False,out_fetched=False),indent=2)+'\n')
print(json.dumps(dict(verify_exit=0,artifacts={n:v for n,v in receipt.items() if n.startswith('artifacts/')},System_map_uncompressed=pin),indent=2))
