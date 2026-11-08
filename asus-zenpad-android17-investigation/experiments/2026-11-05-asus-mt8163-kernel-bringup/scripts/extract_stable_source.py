#!/usr/bin/env python3
import hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];archive=root/'downloads/mt8163-4.9-dc63af1.tar.gz';dest=root/'sources/kernel'
sha=hashlib.sha256(archive.read_bytes()).hexdigest()
if (dest/'Makefile').exists():
 assert not (root/'sources/kernel-incomplete-bpf').exists()
 dest.rename(root/'sources/kernel-incomplete-bpf')
dest.mkdir(exist_ok=True)
with tarfile.open(archive) as tf:
 members=tf.getmembers();prefix=members[0].name.split('/')[0]+'/'
 for m in members:
  if m.name.rstrip('/')==prefix.rstrip('/'):continue
  assert m.name.startswith(prefix);m.name=m.name[len(prefix):]
  assert not m.name.startswith('/') and '..' not in Path(m.name).parts
  tf.extract(m,dest,filter='data')
(root/'evidence/stable-source-provenance.json').write_text(json.dumps(dict(repo='https://github.com/amazon-oss/android_kernel_amazon_mt8163',commit='dc63af1741072236efb511499f1f0b9dd281d694',archive_sha256=sha,archive_bytes=archive.stat().st_size,source_entries=len(members),role='pre-backport Linux 4.9.337 hardware baseline; Android 17 features not yet ported'),indent=2)+'\n')
print('Stable source extracted:',sha)
