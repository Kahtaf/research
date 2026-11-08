from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
first=R/'artifacts/candidate-delivery'
second=R/'artifacts/reproduction-delivery'
rows={}
for name in ['UNTESTED-target-rescue.img','UNTESTED-target-rescue.p10.raw','rescue.cpio.gz','rescue-sepolicy','file_contexts.bin','rescue.manifest']:
 assert (first/name).read_bytes()==(second/name).read_bytes(),name
 rows[name]=digest(first/name)
a=R/'artifacts/tools-delivery/os-rescue';b=R/'artifacts/daemon-delivery-reproduction/os-rescue'
assert a.read_bytes()==b.read_bytes()
rows['os-rescue']=digest(a)
result=dict(passed=True,byte_identical=rows,
  scope='Changed daemon recompiled; image/policy/compiled contexts independently reassembled. Unchanged proxy and host tools retain prior byte-reproduction evidence.',
  command='aarch64-linux-gnu-gcc -static -O2 -Wall -Wextra -Werror -Wno-unused-function -Wno-misleading-indentation -Wl,--build-id=none source/rescue.c -o artifacts/daemon-delivery-reproduction/os-rescue',
  guest_binaries={p.name:digest(p) for p in [R/'artifacts/tools-delivery/guest-init',R/'artifacts/tools-delivery/target-probe']})
(R/'evidence/reproduction-delivery.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
