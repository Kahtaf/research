from pathlib import Path
import hashlib,json,shutil,tarfile
R=Path(__file__).resolve().parents[1]
S=R.parent/'2026-11-06-asus-stock-gpio28-source-port'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records={}
for name in ['candidate','preimage','patches','tests/generated','inputs/api','inputs/dt-source']:
    for p in (S/name).rglob('*'):
        if p.is_file():
            assert not p.is_symlink()
            rel=str(p.relative_to(S));dest=R/'inputs'/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            assert not dest.exists()
            shutil.copyfile(p,dest)
            assert sha(dest)==sha(p)
            records[rel]=sha(p)
for rel in ['tests/contract.c','evidence/pre-post-pins.json','evidence/input-pins.json','evidence/api-line-receipts.json','evidence/internal-functions-unchanged.json','evidence/HAL-unchanged.json','report/HANDOFF.md']:
    p=S/rel;dest=R/'inputs'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
    assert not dest.exists();shutil.copyfile(p,dest);records[rel]=sha(p)
pins=json.loads((S/'evidence/pre-post-pins.json').read_text())
for v in pins:
    assert sha(S/'candidate'/v['path'])==v['post_sha256']
    assert (sha(S/'preimage'/v['path']) if (S/'preimage'/v['path']).exists() else None)==v['pre_sha256']
assert len(pins)==7
(R/'evidence/local-input-pins.json').write_text(json.dumps(records,indent=2)+'\n')
with tarfile.open(R/'inputs.tar.gz','w:gz') as t:
    t.add(R/'inputs',arcname='inputs')
print('Pinned',len(records),'public files; all seven exact pre/post identities checked')
