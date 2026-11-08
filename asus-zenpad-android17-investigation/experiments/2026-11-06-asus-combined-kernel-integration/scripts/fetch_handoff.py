from pathlib import Path
import subprocess,tarfile,hashlib,json,shutil
from remote import SSH
R=Path(__file__).resolve().parents[1]
selected=['manifest.json','Image.gz-dtb','resolved.config','kernel.release','asus-p00a.dtb','dt-receipt.json','dt-verifier.log','config-receipt.json','symbols.json','source-receipt.json','combined-from-active-soc.patch','combined-source-changes.tar.gz','runtime-source-preservation.json','staged-product-receipt.json','network-applied.json','patches','runtime-evidence','build-logs','final-process-status.json']
archive=R/'artifacts/handoff-r5.tar.gz'
assert not archive.exists()
with archive.open('xb') as f:
 subprocess.run(SSH+['tar -czf - -C /srv/android/asus-build-continuation/integration-r5 '+' '.join(selected)],stdout=f,check=True)
assert archive.stat().st_size<25_000_000
out=R/'artifacts/handoff-r5';out.mkdir()
with tarfile.open(archive) as t:
 for m in t.getmembers():
  p=Path(m.name);assert not p.is_absolute() and '..' not in p.parts and not m.issym() and not m.islnk(),m.name
 t.extractall(out,filter='data')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((out/'manifest.json').read_text())
assert sha(out/'Image.gz-dtb')==m['image']['sha256']
assert (out/'Image.gz-dtb').stat().st_size==m['image']['bytes']
for name,key in [('resolved.config','config_sha256'),('source-receipt.json','source_receipt_sha256'),('staged-product-receipt.json','staged_product_receipt_sha256'),('runtime-source-preservation.json','runtime_source_receipt_sha256'),('asus-p00a.dtb','dtb_sha256')]:assert sha(out/name)==m[key]
s=json.loads((out/'source-receipt.json').read_text());assert sha(out/'combined-from-active-soc.patch')==s['patch_sha256'];assert sha(out/'combined-source-changes.tar.gz')==s['source_archive_sha256']
with tarfile.open(out/'combined-source-changes.tar.gz') as t:
 files={p.name:hashlib.sha256(t.extractfile(p).read()).hexdigest() for p in t.getmembers() if p.isfile()}
 assert files=={p:v['after'] for p,v in s['changes'].items()}
for p,row in json.loads((R/'evidence/frozen-probes-before.json').read_text()).items():assert sha(R.parent/p)==row['sha256']
receipt=dict(archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,downloaded_kernel_sha256=sha(out/'Image.gz-dtb'),source_archive_files_verified=len(files),all_pinned_receipts_verified=True,existing_probes_and_r1_r3_artifacts_unchanged=True,full_SYSTEM_or_data_images_downloaded=False)
(R/'evidence/local-export-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
