from pathlib import Path
import base64,json,subprocess
from vm import R,channel
root=json.loads((R/'evidence/identity.json').read_text())['remote_root']
script=r'''from pathlib import Path
import base64,json
R=Path(ROOT)
names=['evidence/build-status.json','evidence/compiler-receipt.json','evidence/helper-compile.log','evidence/copy-kernel.log','evidence/base-freeze.json','artifacts/init','artifacts/init.unstripped','artifacts/initramfs.cpio.gz']
result={}
for n in names:
 p=R/n
 if p.is_file():
  d=p.read_bytes()
  if n.endswith('copy-kernel.log'):d=b'\n'.join(d.splitlines()[:8])
  result[n]=base64.b64encode(d).decode()
print(json.dumps(result))
'''.replace('ROOT',repr(root))
p=subprocess.run(channel()+['python3 -B -'],input=script,text=True,capture_output=True);print(p.stderr);p.check_returncode()
for n,d in json.loads(p.stdout).items():(R/n).write_bytes(base64.b64decode(d))
print((R/'evidence/compiler-receipt.json').read_text());print((R/'evidence/copy-kernel.log').read_text())
