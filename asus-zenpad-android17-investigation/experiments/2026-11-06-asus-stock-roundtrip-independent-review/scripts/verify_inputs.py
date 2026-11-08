from pathlib import Path
import sys,json,hashlib,datetime,importlib.util
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent;C=W/'2026-11-06-asus-stock-roundtrip-continuation';P=W/'2026-11-06-asus-stock-programmatic-control'
sys.path.insert(0,str(C/'source/service'))
import controller as c
import fixed as f
review=C/'evidence/service/runs/20261106T193652Z-6bab3892d6af6400/review-template.json'
old=json.loads(review.read_text());current=c.contract()
assert old['contract']==current
assert all(v is False for v in old['parent_review'].values() if type(v) is bool)
stock,candidate,records=f.fixed_inputs()
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'device_contacted':False,'contract_matches_template':True,
        'real_flags_all_false':True,'stock_bytes':len(stock),'stock_sha256':f.sha(stock),'padded_candidate_bytes':len(candidate),
        'padded_candidate_sha256':f.sha(candidate),'source_and_evidence_sha256':c.source_pins(),'fixed_inputs':records}
extra=['2026-11-06-asus-stock-roundtrip-continuation/HANDOFF.md',
'2026-11-06-asus-stock-roundtrip-continuation/evidence/service/parent-fault-replay.json',
'2026-11-06-asus-android17-orchestration/evidence/stock-control-runtime-20261106.json',
'2026-11-06-asus-android17-orchestration/evidence/explicit-recovery-inverse-runtime-20261106.json',
'2026-11-06-asus-factory-state-preservation/evidence/parent-preservation-acceptance.json']
result['additional_evidence_sha256']={p:f.sha(f.read(W/p)) for p in extra}
# Read the saved JSON evidence fully; never traverse private paths or full SYSTEM.
for p in list(result['source_and_evidence_sha256'])+extra:
 if p.endswith('.json'):json.loads((W/p).read_text())
proof=json.loads((P/'evidence/service/firmware-audit.json').read_text())
for name,item in proof['root_rc'].items():
 data=f.read(P/item['artifact']);assert len(data)==item['bytes'] and f.sha(data)==item['sha256']
result['rc_artifacts_verified']=len(proof['root_rc'])
sys.path.insert(0,str(P/'source/service'))
from elfaudit import ELF
for key,expected in proof['region_sha256'].items():
 name,region=key.split(':');start,end=[int(v,16) for v in region.split('-')]
 elf=ELF(P/'artifacts/service'/('boot-init' if name=='init' else 'boot-sbin_adbd'))
 assert f.sha(elf.bytes(start,end))==expected
init=ELF(P/'artifacts/service/boot-init')
assert [hex(i.address) for i in init.instructions() if i.mnemonic in ('b','bl') and i.op_str=='#0x421f40']==['0x408818']
result['elf_regions_verified']=len(proof['region_sha256'])
result['bcb_writer_direct_callers']=['0x408818']
(R/'evidence/input-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('source_and_evidence_sha256','additional_evidence_sha256','fixed_inputs')}))
