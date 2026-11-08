from pathlib import Path
import json,hashlib,shutil,tarfile,datetime
R=Path('/srv/android/asus-genuine-service-runtime');A=R/'artifacts';A.mkdir(exist_ok=True);D=A/'export-final-r3';D.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(src,rel):
 dst=D/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
for src in (R/'source').iterdir():
 if src.is_file() and src.suffix in ['.py','.c']:copy(src,Path('source')/src.name)
for src in (R/'evidence').iterdir():
 if src.is_file() and src.name != 'export-receipt.json' and src.suffix in ['.json','.log','.diff']:copy(src,Path('evidence')/src.name)
for run in R.glob('run-boot-r*'):
 for src in run.iterdir():
  if src.is_file() and src.suffix in ['.json','.log','.py','.c']:copy(src,Path('runs')/run.name/src.name)
for src in (R/'inputs/provenance').iterdir():
 if src.is_file():copy(src,Path('provenance')/src.name)
for n in ['README.md','REPORT.md','HANDOFF.json','PARENT-REQUEST.md']:copy(R/n,Path(n))
# Public generated metadata plus its sources/commands are compact review artifacts.
root=R/'inputs/boot-r9/root'
for pat in ['system/**/etc/selinux/*service_contexts','system/**/etc/vintf/manifest.xml']:
 for src in root.glob(pat):
  if src.is_file():copy(src,Path('generated')/src.relative_to(root))
manifest=[dict(path=str(f.relative_to(D)),bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(D.rglob('*')) if f.is_file()]
(D/'manifest.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),entries=manifest),indent=2));archive=A/'evidence-final-r3.tar.gz'
with tarfile.open(archive,'w:gz') as tar:tar.add(D,arcname='frozen-final-r3')
receipt=dict(path=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),manifest_sha256=sha(D/'manifest.json'),payload_files=len(manifest),large_guest_files_exported=False)
(R/'evidence/export-receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
