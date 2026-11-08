from pathlib import Path
import subprocess,json,hashlib,os
R=Path('/srv/android/asus-retained-report-control-20261107')
assert not (R/'artifacts/init').exists()
cmd=['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Wl,--build-id=none','-fno-ident',str(R/'source/init.c'),'-o',str(R/'artifacts/init')]
p=subprocess.run(cmd,capture_output=True,text=True,timeout=120,env={**os.environ,'LC_ALL':'C'})
receipt=dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,compiler_invocations=1)
if p.returncode==0:
 data=(R/'artifacts/init').read_bytes();receipt['init']=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
(R/'evidence/helper-compile.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert p.returncode==0,receipt
print(json.dumps(receipt))
