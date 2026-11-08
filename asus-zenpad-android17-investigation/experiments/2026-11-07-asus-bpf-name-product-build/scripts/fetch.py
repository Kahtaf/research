from pathlib import Path
import base64,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run
payload=json.loads(run('''from pathlib import Path
import base64,hashlib,json
own=Path('/srv/android/asus-bpf-name-product-build-20261107')
assert (own/'evidence/final-report.json').is_file() or (own/'evidence/FAILED.json').is_file()
files={p.name:base64.b64encode(p.read_bytes()).decode() for p in (own/'evidence').iterdir() if p.is_file() and p.suffix in ('.json','.tsv')}
p=own/'logs/native.log';data=p.read_bytes()
lines=[line for line in data.decode(errors='replace').splitlines() if ('system/bpf/loader:' in line or 'system/lib64/libbpf_android.so' in line or 'Target system fs image:' in line or 'Install system fs image:' in line or 'Build Succeeded:' in line or 'build completed successfully' in line)]
log={'path':str(p),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'selected_native_lines':lines,'tail':data[-3000:].decode(errors='replace')}
print(json.dumps({'files':files,'native_log':log}))
'''))
for name,encoded in payload['files'].items():
 p=ROOT/'evidence'/name;data=base64.b64decode(encoded)
 if p.exists():assert p.read_bytes()==data
 else:p.write_bytes(data)
(ROOT/'evidence/native-log-excerpt.json').write_text(json.dumps(payload['native_log'],indent=2)+'\n')
report=json.loads((ROOT/'evidence/final-report.json').read_text())
table=ROOT/'evidence/system-1MiB-chunks.tsv'
assert hashlib.sha256(table.read_bytes()).hexdigest()==report['system']['chunk_table']['sha256']
pins={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (ROOT/'evidence').iterdir() if p.is_file()}
(ROOT/'evidence/local-export-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
print(json.dumps({'status':report['status'],'fetched_public_files':len(payload['files']),'chunk_table_bytes':table.stat().st_size,'chunk_table_transfer_sha256_verified':True,'native_log_sha256':payload['native_log']['sha256']}))
