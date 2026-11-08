from transport import run,L,R
import base64,json,hashlib
# Execute only after the complete owned build reports success. No retries or relaunch.
verifier=(L/'scripts/verify_remote.py').read_text()
s='''from pathlib import Path
import subprocess,json,base64,gzip
R=Path(PREFIX)
assert json.loads((R/'evidence/build-status.json').read_text())['status']=='complete'
(R/'scripts/verify_remote.py').write_text(VERIFIER)
p=subprocess.run(['python3','-B',str(R/'scripts/verify_remote.py')],capture_output=True,text=True)
(R/'evidence/verify.stdout').write_text(p.stdout);(R/'evidence/verify.stderr').write_text(p.stderr)
if p.returncode:
 print(json.dumps({'verification_exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}));raise SystemExit(0)
files={}
for n,dst in [('Image.gz-dtb','artifacts/Image.gz-dtb'),('.config','artifacts/resolved.config'),('dts/mediatek/asus-p00a.dtb','artifacts/asus-p00a.dtb')]:
 src=R/'out'/('.config' if n=='.config' else 'arch/arm64/boot/'+n);files[dst]=src.read_bytes()
for p in (R/'evidence').iterdir():
 if p.suffix in ['.json','.txt','.config'] or p.name in ['verify.stdout','verify.stderr','prepare.stdout','prepare.stderr']:
  files['evidence/'+p.name]=p.read_bytes()
 elif p.suffix=='.log':files['evidence/'+p.name+'.gz']=gzip.compress(p.read_bytes(),mtime=0)
files['patches/combined-from-bmc.patch']=(R/'patches/combined-from-bmc.patch').read_bytes()
for n in ['compile.h','utsrelease.h']:files['evidence/'+n]=(R/'out/include/generated'/n).read_bytes()
assert sum(map(len,files.values()))<12*1024**2,'compact return exceeds 12 MiB'
print(json.dumps({'verification_exit':0,'total_bytes':sum(map(len,files.values())),'files':{n:base64.b64encode(b).decode() for n,b in files.items()}}))
'''.replace('PREFIX',repr(R)).replace('VERIFIER',repr(verifier))
r=json.loads(run(s))
if r['verification_exit']:
 (L/'evidence/verification-failure.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));raise SystemExit(1)
receipt={}
for name,b in r['files'].items():
 p=L/name;assert p.resolve().is_relative_to(L.resolve());data=base64.b64decode(b);p.write_bytes(data);receipt[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
(L/'evidence/local-delivery.json').write_text(json.dumps({'total_bytes':r['total_bytes'],'files':receipt},indent=2,sort_keys=True)+'\n')
# Local checks bind downloaded artifacts to the actual VM verification receipt.
v=json.loads((L/'evidence/verification.json').read_text())
for local,remote in [('Image.gz-dtb','arch/arm64/boot/Image.gz-dtb'),('resolved.config','.config'),('asus-p00a.dtb','arch/arm64/boot/dts/mediatek/asus-p00a.dtb')]:
 data=(L/'artifacts'/local).read_bytes();assert {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}==v['artifacts'][remote]
print(json.dumps({'status':'delivered and local hashes matched','total_bytes':r['total_bytes'],'kernel':receipt['artifacts/Image.gz-dtb']},indent=2))
