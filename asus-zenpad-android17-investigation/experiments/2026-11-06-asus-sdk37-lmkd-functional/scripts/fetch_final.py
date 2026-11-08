from pathlib import Path
import subprocess,tarfile,json,hashlib
P=Path(__file__).resolve().parent.parent;ns={};t=(P/'scripts/remote.py').read_text();exec(t[:t.index('r=subprocess')],ns)
(P/'artifacts').mkdir(exist_ok=True)
for name in ['evidence-r1.tar.gz','receipt-r1.json']:
 with (P/'artifacts'/name).open('wb') as f:subprocess.run(ns['SSH']+['cat /srv/android/asus-sdk37-lmkd-functional/exports/'+name],stdout=f,check=True)
r=json.loads((P/'artifacts/receipt-r1.json').read_text());archive=P/'artifacts/evidence-r1.tar.gz';assert hashlib.sha256(archive.read_bytes()).hexdigest()==r['archive_sha256'];dest=P/'artifacts/frozen';dest.mkdir()
with tarfile.open(archive) as a:a.extractall(dest,filter='data')
m=json.loads((dest/'export-manifest.json').read_text())
for n,x in m['files'].items():
 f=dest/n;assert f.stat().st_size==x['bytes'];assert hashlib.sha256(f.read_bytes()).hexdigest()==x['sha256'],n
(P/'evidence/export-verification.json').write_text(json.dumps({'verified':True,**r},indent=2));print(json.dumps(r,indent=2))
