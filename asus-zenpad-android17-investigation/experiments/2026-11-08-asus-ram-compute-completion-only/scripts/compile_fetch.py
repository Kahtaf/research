"""One owned-channel dispatch/compile/fetch; no kernel copy or build."""
from pathlib import Path
import base64,hashlib,json,subprocess
from vm import R,channel
B=R.parent/'2026-11-08-asus-normal-ram-compute-control'
root=json.loads((R/'evidence/identity.json').read_text())['remote_root']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={'kernel/arch/arm64/kernel/'+n:sha(B/'source/reused'/n) for n in ['asus_retained_trace.c','asus_entry_tag.h']}
(R/'evidence/remote-source-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
files={str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode() for p in [R/'source/init.c',R/'source/bootformat.py',R/'scripts/compile_remote.py',R/'evidence/remote-source-pins.json']}
script='''from pathlib import Path
import base64,json,subprocess
R=Path(DEST);assert not R.exists(),'one dispatch';R.mkdir()
for n in ['source','scripts','evidence','artifacts']:(R/n).mkdir()
for n,data in FILES.items():(R/n).write_bytes(base64.b64decode(data))
p=subprocess.run(['python3','-B',str(R/'scripts/compile_remote.py')],capture_output=True,text=True)
names=['evidence/build-status.json','evidence/compiler-receipt.json','evidence/helper-compile.stdout','evidence/helper-compile.stderr','evidence/helper-strip.stdout','evidence/helper-strip.stderr','evidence/helper-scoped.disasm','evidence/reused-kernel-scoped.disasm','evidence/remote-reuse.json','artifacts/init','artifacts/init.unstripped','artifacts/initramfs.cpio.gz']
print(json.dumps(dict(exit=p.returncode,stdout=p.stdout,stderr=p.stderr,files={n:base64.b64encode((R/n).read_bytes()).decode() for n in names if (R/n).is_file()})))
'''.replace('DEST',repr(root)).replace('FILES',repr(files))
with (R/'evidence/dispatch.json').open('x') as f:json.dump(dict(remote_root=root,one_dispatch=True),f)
p=subprocess.run(channel()+['python3 -B -'],input=script,text=True,capture_output=True)
(R/'evidence/ssh-compile.stderr').write_text(p.stderr);p.check_returncode()
d=json.loads(p.stdout);pins={}
for n,value in d.pop('files').items():
 data=base64.b64decode(value);(R/n).write_bytes(data);pins[n]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
(R/'evidence/fetch-receipt.json').write_text(json.dumps(dict(result=d,files=pins),indent=2)+'\n')
print(json.dumps(d));assert d['exit']==0
