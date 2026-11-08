from pathlib import Path
import json,hashlib,shutil,datetime
R=Path('/srv/android/asus-bmc156-full-kernel-r1');S=R/'export';X=R/'export-compact'
assert R.resolve()==R and S.resolve()==S and not X.exists() and shutil.disk_usage(R).free>1024**3
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((S/'MANIFEST.json').read_text());X.mkdir()
for rel,v in m['files'].items():
 p=S/rel;assert sha(p)==v['sha256']
 if rel=='evidence/System.map.gz':continue
 d=X/rel;assert d.resolve().is_relative_to(X);d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d)
shutil.copyfile(R/'scripts/compact_export.py',X/'scripts/compact_export.py')
(X/'evidence/compact-export.json').write_text(json.dumps(dict(original_export_preserved=str(S),original_manifest_sha256=sha(S/'MANIFEST.json'),omitted_local_payload={'path':'evidence/System.map.gz',**m['files']['evidence/System.map.gz']},complete_System_map_retained_on_VM=str(R/'out/System.map'),full_System_map_pin='evidence/full-verification.json artifacts.System.map',selected_linked_symbol_receipts_retained=True),indent=2)+'\n')
files={str(p.relative_to(X)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in X.rglob('*') if p.is_file()};size=sum(v['bytes'] for v in files.values());assert size<12_000_000
(X/'MANIFEST.json').write_text(json.dumps(dict(files=files,total_bytes=size,created=datetime.datetime.now(datetime.timezone.utc).isoformat()),sort_keys=True,indent=2)+'\n')
print('COMPACT EXPORT',len(files),'files',size,'bytes',sha(X/'MANIFEST.json'))
