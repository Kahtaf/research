#!/usr/bin/env python3
"""Package reviewable staged inputs only; no deployment or remote actions."""
import gzip, hashlib, json, pathlib, tarfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts'; OUT.mkdir(exist_ok=True)
files=[]
for p in sorted((ROOT/'staged/device').rglob('*')):
 if p.is_file(): files.append((p, str(p.relative_to(ROOT/'staged'))))
for p in sorted((ROOT/'staged/patches').glob('*.patch')):
 files.append((p,'kernel-patches/'+p.name))
for n in ['README.md','REPORT.md','PROVENANCE.md']:
 files.append((ROOT/n,'docs/'+n))
# Includes the GPL license for the carried-forward source patches.
files.append((ROOT/'sources/asus-gpl/kernel-3.18/COPYING','kernel-patches/COPYING'))
for n in ['stock-input-manifest.json', 'kernel-gate.json', 'module-manifest.json', 'platform-module-index.json', 'current-fsmgr-legacy-api.json', 'validation.json']:
 files.append((ROOT/'evidence'/n, 'evidence/'+n))
manifest=[]
archive=OUT/'p00a-connectivity-staging.tar.gz'
with archive.open('wb') as raw, gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as zipped, tarfile.open(fileobj=zipped,mode='w|') as tar:
 for p,name in files:
  data=p.read_bytes()
  info=tar.gettarinfo(str(p),arcname=name)
  info.uid=info.gid=0; info.uname=info.gname=''; info.mtime=0;info.mode=0o644
  with p.open('rb') as f:tar.addfile(info,f)
  manifest.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
(OUT/'files.json').write_text(json.dumps(manifest,indent=2)+'\n')
(OUT/'SHA256SUMS').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
print('Packaged',len(files),'files,',archive.stat().st_size,'bytes')
