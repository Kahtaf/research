from pathlib import Path
import tarfile,json,hashlib
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
seal=sha(R/'inputs/kit-pins.json');assert seal=='f55aedf8ac9d2a513e3663230db0b9d802e72b5df512fc0db6b3714331a7efa4'
archive=R/'artifacts/r8-continuation-compact.tar.gz'
files=[]
for d in ['scripts','inputs','tests','source','evidence']:
 files.extend(p for p in (R/d).rglob('*') if p.is_file() and '__pycache__' not in p.parts and not any(q.startswith('TEST_ONLY-') for q in p.parts))
files.extend(R/n for n in ['README.md','HANDOFF.md','REPORT.md','artifacts/wpa-sdk37-candidate.o'])
with tarfile.open(archive,'x:gz') as tar:
 for p in sorted(files):tar.add(p,arcname=str(p.relative_to(R)),recursive=False)
pins=json.loads((R/'inputs/kit-pins.json').read_text())
with tarfile.open(archive,'r:gz') as tar:
 for rel,digest in pins.items():assert hashlib.sha256(tar.extractfile(rel).read()).hexdigest()==digest,rel
result=dict(kit_pins_sha256=seal,pinned_files=len(pins),archive=dict(path=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,files=len(files)),every_pinned_archive_member_verified=True,fixture_object_sha256=sha(R/'artifacts/wpa-sdk37-candidate.o'),staging_manifest_sha256=sha(R/'inputs/r8-staging-manifest.json'),r7_preservation_sha256=sha(R/'inputs/r7-preservation.json'),approval_authored=False,product_build_started=False)
(R/'kit-seal.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');Path(str(archive)+'.sha256').write_text(sha(archive)+'  '+archive.name+'\n');print(json.dumps(result,indent=2))
