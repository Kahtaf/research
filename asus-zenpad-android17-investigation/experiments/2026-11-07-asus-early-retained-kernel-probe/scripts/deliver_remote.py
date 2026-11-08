from pathlib import Path
import sys,json,subprocess,hashlib
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parent/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run,SSH
remote=Path('/srv/android/asus-early-retained-kernel-probe-20261107')
pack=json.loads((R/'evidence/packaging-receipt.json').read_text())
# Upload only this spike's new public candidate; padded p10 remains on the VM.
code='''from pathlib import Path
import sys,hashlib,json
R=Path('/srv/android/asus-early-retained-kernel-probe-20261107');A=R/'artifacts'
expected=EXPECTED
p=A/'candidate.img';assert not p.exists()
x=sys.stdin.buffer.read();assert len(x)==expected['image']['bytes'] and hashlib.sha256(x).hexdigest()==expected['image']['sha256']
p.write_bytes(x)
full=x+bytes(expected['full_p10']['bytes']-len(x));q=A/'candidate.p10.raw';assert not q.exists();q.write_bytes(full)
result={}
for f in [p,q]:
 z=f.read_bytes();result[f.name]=dict(bytes=len(z),sha256=hashlib.sha256(z).hexdigest())
assert result['candidate.img']==expected['image'] and result['candidate.p10.raw']==expected['full_p10']
print(json.dumps(result))
'''.replace('EXPECTED',repr(dict(image=pack['image'],full_p10=pack['full_p10'])))
# Single quoted Python command uses shlex.quote; no command substitutions.
import shlex
p=subprocess.run(SSH+['python3 -B -c '+shlex.quote(code)],input=(R/'artifacts/candidate.img').read_bytes(),capture_output=True)
assert p.returncode==0,p.stderr.decode()
receipt=dict(remote_prefix=str(remote),actual_readback=json.loads(p.stdout),padded_p10_local=False,private_parent_input_uploaded=False)
(R/'evidence/remote-delivery.json').write_text(json.dumps(receipt,indent=2)+'\n')
# Keep the public patch, adapter and receipts alongside the candidate remotely.
names=['source/install.py','source/install.diff','source/package_probe.py','source/bootformat.py','source/fdt.py','source/adb','source/legacy_adb.py','evidence/packaging-receipt.json','evidence/install-plan.json','README.md']
payload={n:(R/n).read_text() for n in names}
print(run('''from pathlib import Path
R=Path('/srv/android/asus-early-retained-kernel-probe-20261107')
for n,s in PAYLOAD.items():(R/n).write_text(s)
print('public support delivery complete')
'''.replace('PAYLOAD',repr(payload))))
print(json.dumps(receipt))
