"""Seal documentation/evidence and make compact delivery; never includes images."""
from pathlib import Path
import hashlib,json,tarfile
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
seal=sha(R/'inputs/kit-pins.json')
assert seal=='9287a07d243a9d70abefa0102de160d88af712a574c7fab6032ce9b36920f617'
r=dict(kit_pins_sha256=seal,pinned_files=len(json.loads((R/'inputs/kit-pins.json').read_text())),
       r3_kit_pins_sha256='a00ea8d7c944d45e3035296c81b31a369f13bde830f88a7165b0d7542960717c',
       staged_manifest_sha256=sha(R/'inputs/r7-staging-manifest.json'),
       builder_kit='/srv/android/asus-reviewed-build-kit/r7',builder_staging='/srv/android/asus-product-integration-staging/r7',
       native_build_started=False,actual_product_dumpvars_run=False,parent_failure_acceptance_created=False,
       active_sources_mutated=False,device_accessed=False,flash_ready=False)
(R/'kit-seal.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
files=[p for p in sorted(R.rglob('*')) if p.is_file() and p.relative_to(R).parts[0]!='artifacts' and p.name!='ARTIFACTS.sha256' and '__pycache__' not in p.parts and not any(x.startswith('TEST_ONLY-') for x in p.parts)]
(R/'ARTIFACTS.sha256').write_text(''.join(sha(p)+'  '+str(p.relative_to(R))+'\n' for p in files))
archive=R/'artifacts/r7-continuation-compact.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in files+[R/'ARTIFACTS.sha256']:tar.add(p,arcname=str(p.relative_to(R)),recursive=False)
(archive.parent/(archive.name+'.sha256')).write_text(sha(archive)+'  '+archive.name+'\n')
with tarfile.open(archive,'r:gz') as tar:
 members=tar.getmembers();assert len(members)==len(files)+1
 for p in files+[R/'ARTIFACTS.sha256']:
  f=tar.extractfile(str(p.relative_to(R)));assert hashlib.sha256(f.read()).hexdigest()==sha(p)
print(json.dumps(dict(kit_seal=seal,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,archive_files=len(files)+1),indent=2))
