from pathlib import Path
import importlib.util,subprocess,tarfile,io,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('builder_remote',ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
script="""from pathlib import Path
import tarfile,sys
p=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106/supplement-qualified-r2')
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as t:t.add(p,arcname='supplement-qualified-r2')
"""
p=subprocess.run(m.SSH+['python3 -B -'],input=script.encode(),capture_output=True);assert p.returncode==0,p.stderr.decode()
archive=ROOT/'artifacts/supplement-qualified-r2.tar.gz';assert not archive.exists();archive.write_bytes(p.stdout)
with tarfile.open(fileobj=io.BytesIO(p.stdout),mode='r:gz') as t:
 for member in t.getmembers():
  q=Path(member.name);assert not q.is_absolute() and '..' not in q.parts and not member.issym() and not member.islnk()
 t.extractall(ROOT/'artifacts',filter='data')
handoff=ROOT/'artifacts/supplement-qualified-r2';manifest=json.loads((handoff/'manifest.json').read_text());bad=[]
for path,v in manifest['files'].items():
 data=(handoff/path).read_bytes()
 if hashlib.sha256(data).hexdigest()!=v['sha256'] or len(data)!=v['bytes']:bad.append(path)
assert not bad,bad
result={'manifest_sha256':hashlib.sha256((handoff/'manifest.json').read_bytes()).hexdigest(),'archive_sha256':hashlib.sha256(p.stdout).hexdigest(),'archive_bytes':len(p.stdout),'verified_files':len(manifest['files'])}
(ROOT/'evidence/local-handoff-verification-r2.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
