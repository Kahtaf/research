"""Read only small pinned inputs and existing unapproved template; never main()."""
import sys
sys.dont_write_bytecode=True
import ast,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R.parent/'2026-11-06-asus-stock-helper-dispatch-fix'
sys.path.insert(0,str(P/'source/service'))
import controller as C,fixed as F
before=json.loads((R/'evidence/parent-before.json').read_text())
after={str(p.relative_to(R.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in P.rglob('*') if p.is_file()}
assert before==after,'Parent changed during review'
pins=json.loads((P/'evidence/source-pins.json').read_text())
for name,digest in pins.items():assert F.sha((P/name).read_bytes())==digest,name
contract=C.contract()
template_path=P/'evidence/service/runs/20261106T203701Z-fc9f8eb839d44400/review-template.json'
template=json.loads(template_path.read_text());assert template['contract']==contract
flags={k:v for k,v in template['parent_review'].items() if type(v) is bool}
assert flags and not any(flags.values())
source=F.read(F.E.HELPER);assert F.sha(source)==F.E.HELPER_HASH
assert F.sha(F.read(F.E.ROOT_BINARY))==F.E.ROOT_BINARY_HASH
calls=[]
for n in ast.walk(ast.parse(source)):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='subprocess':
        calls.append(dict(line=n.lineno,method=n.func.attr,keywords=[k.arg for k in n.keywords]))
receipt=dict(parent_files_unchanged=len(before),source_pins=pins,contract_hashes_checked=len(contract['source_and_evidence_sha256']),template=str(template_path),template_sha256=F.sha(template_path.read_bytes()),live_flags=flags,helper_sha256=F.E.HELPER_HASH,engine_sha256=F.ENGINE_SHA,root_binary_sha256=F.E.ROOT_BINARY_HASH,helper_subprocess_calls=sorted(calls,key=lambda c:c['line']),device_contacted=False,large_image_rehash=False,firmware_replay=False)
(R/'evidence/provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k in ('parent_files_unchanged','contract_hashes_checked','device_contacted','live_flags')}))
