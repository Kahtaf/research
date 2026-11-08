#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,difflib,tarfile,gzip,io
s=Path(__file__).resolve().parents[1]
payload=[s/'Android.bp',*sorted((s/'src').glob('*')),*sorted(p for p in (s/'staging').rglob('*') if p.is_file())]
pre=[];patch=[]
for p in payload:
 rel=str(p.relative_to(s));dest='device/asus/p00a/audio/'+rel;data=p.read_bytes()
 pre.append({'destination':dest,'preimage':'MUST_NOT_EXIST','preimage_observed':False,'new_sha256':hashlib.sha256(data).hexdigest(),'mode':'100644'})
 patch.extend(difflib.unified_diff([],data.decode().splitlines(keepends=True),fromfile='/dev/null',tofile='b/'+dest))
(s/'patch-preimages.json').write_text(json.dumps({'contract':'Additive future stage only; stop if any destination exists. No existing product/kernel files patched. Parent owns includes/qualification.','files':pre},indent=2)+'\n')
(s/'staging-additions.patch').write_text(''.join(patch))
# Inventory includes evidence ELFs, not large native sanitizer executable or private data.
files=[p for p in sorted(s.rglob('*')) if p.is_file() and p.name not in ['ARTIFACTS.json'] and 'bundle' not in p.relative_to(s).parts and p.relative_to(s).as_posix()!='evidence/host/transport_test']
manifest=[{'path':str(p.relative_to(s)),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
(s/'ARTIFACTS.json').write_text(json.dumps({'status':'gated_transport_stage_no_hardware_claim','files':manifest},indent=2)+'\n')
files.append(s/'ARTIFACTS.json');(s/'bundle').mkdir(exist_ok=True)
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w') as t:
 for p in sorted(files):
  info=t.gettarinfo(str(p),arcname='p00a-audio-stage/'+str(p.relative_to(s)));info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
  with p.open('rb') as f:t.addfile(info,f)
out=s/'bundle/p00a-audio-stage.tar.gz';out.write_bytes(gzip.compress(buf.getvalue(),mtime=0))
sha=hashlib.sha256(out.read_bytes()).hexdigest();(s/'bundle/SHA256SUMS').write_text(sha+'  p00a-audio-stage.tar.gz\n')
print('BUNDLE',out, out.stat().st_size,'bytes SHA256',sha)
