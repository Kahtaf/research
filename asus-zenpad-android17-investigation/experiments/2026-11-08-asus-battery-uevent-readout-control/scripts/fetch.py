from pathlib import Path
import base64,gzip,hashlib,json,subprocess
from vm import R,channel
I=json.loads((R/'evidence/identity.json').read_text())
s='''from pathlib import Path
import base64,gzip,hashlib,json
R=Path(ROOT);O=R/'out';E=R/'evidence'
s=json.loads((E/'build-status.json').read_text());assert s['status']=='complete' and s['kernel_builds']==1 and s['helper_compiles']==0
files={}
for p in E.iterdir():
 if p.is_file():
  assert p.stat().st_size<2*1024**2,(p.name,p.stat().st_size)
  files['evidence/'+p.name]=p.read_bytes()
files['artifacts/Image.gz-dtb']=(O/'arch/arm64/boot/Image.gz-dtb').read_bytes()
files['artifacts/resolved.config']=(O/'.config').read_bytes()
m=(O/'System.map').read_bytes();files['artifacts/System.map.gz']=gzip.compress(m,compresslevel=9,mtime=0)
files['evidence/System.map-uncompressed.json']=(json.dumps(dict(bytes=len(m),sha256=hashlib.sha256(m).hexdigest()),indent=2)+'\\n').encode()
print(json.dumps({n:base64.b64encode(d).decode() for n,d in files.items()}))
'''.replace('ROOT',repr(I['remote_root']))
p=subprocess.run(channel()+['python3 -B -'],input=s,text=True,capture_output=True);(R/'evidence/fetch.stderr').write_text(p.stderr);p.check_returncode();pins={}
for n,v in json.loads(p.stdout).items():
 b=base64.b64decode(v);p=R/n;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,n
 else:p.write_bytes(b)
 pins[n]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
(R/'evidence/fetch-receipt.json').write_text(json.dumps(pins,indent=2)+'\n');print('Small kernel/config/genuine compressed System.map and focused evidence fetched; vmlinux stays remote')
