from pathlib import Path
import base64,gzip,hashlib,json,subprocess
from vm import R,channel
root=json.loads((R/'evidence/identity.json').read_text())['remote_root']
script=r'''from pathlib import Path
import base64,gzip,hashlib,json
R=Path(ROOT);O=R/'out';E=R/'evidence'
status=json.loads((E/'build-status.json').read_text());assert status['status']=='complete'
files={}
for n in ['build-status.json','compiler-receipt.json','helper-compile.log','build-receipt.json','base-freeze.json','copy-receipt.json','space-receipt.json','first-attempt-build-status.json','compile-1.log','helper-scoped.disasm','helper-symbols.txt','kernel-scoped.disasm','retained-object.disasm','retained-object.nm','rt-default-source.txt']:
 p=E/n;assert p.stat().st_size<2*1024**2,(n,p.stat().st_size);files['evidence/'+n]=p.read_bytes()
files['artifacts/Image.gz-dtb']=(O/'arch/arm64/boot/Image.gz-dtb').read_bytes()
files['artifacts/resolved.config']=(O/'.config').read_bytes()
m=(O/'System.map').read_bytes();files['artifacts/System.map.gz']=gzip.compress(m,compresslevel=9,mtime=0)
files['evidence/System.map-uncompressed.json']=(json.dumps(dict(bytes=len(m),sha256=hashlib.sha256(m).hexdigest()),indent=2)+'\n').encode()
print(json.dumps({n:base64.b64encode(d).decode() for n,d in files.items()}))
'''.replace('ROOT',repr(root))
p=subprocess.run(channel()+['python3 -B -'],input=script,text=True,capture_output=True);assert not p.returncode,p.stderr
pins={}
for n,data in json.loads(p.stdout).items():
 d=base64.b64decode(data);(R/n).write_bytes(d);pins[n]=dict(bytes=len(d),sha256=hashlib.sha256(d).hexdigest())
(R/'evidence/fetch-receipt.json').write_text(json.dumps(pins,indent=2)+'\n')
b=json.loads((R/'evidence/build-receipt.json').read_text());print(json.dumps(dict(changed_objects=b['changed_objects'],space=json.loads((R/'evidence/space-receipt.json').read_text()),builds=[status if False else b['helper_compiles'],b['kernel_builds']]),indent=2))
