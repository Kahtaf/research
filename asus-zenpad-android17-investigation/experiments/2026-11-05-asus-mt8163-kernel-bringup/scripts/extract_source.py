#!/usr/bin/env python3
import hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
archive=root/'downloads/mt8163-4.9-a81e526.tar.gz'
sha=hashlib.sha256(archive.read_bytes()).hexdigest()
dest=root/'sources/kernel';dest.mkdir(exist_ok=True)
with tarfile.open(archive) as tf:
 members=tf.getmembers();prefix=members[0].name.split('/')[0]+'/'
 for m in members:
  if m.name.rstrip('/')==prefix.rstrip('/'):continue
  assert m.name.startswith(prefix)
  m.name=m.name[len(prefix):]
  assert not m.name.startswith('/') and '..' not in Path(m.name).parts
  tf.extract(m,dest,filter='data')
(root/'evidence/source-provenance.json').write_text(json.dumps(dict(repo='https://github.com/amazon-oss/android_kernel_amazon_mt8163',commit='a81e526957ef342c4ea0c7ff5a3e95366427d0cd',archive_url='https://codeload.github.com/amazon-oss/android_kernel_amazon_mt8163/tar.gz/a81e526957ef342c4ea0c7ff5a3e95366427d0cd',archive_sha256=sha,archive_bytes=archive.stat().st_size,source_entries=len(members)),indent=2)+'\n')
print('Source extracted:',len(members),'entries; archive SHA256:',sha)
