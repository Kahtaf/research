"""Add a corruption negative control to the disposable ext4 base, never original inputs."""
from pathlib import Path
import subprocess as s,json,hashlib
r=Path('/srv/android/asus-android17-runtime-prereqs');p=json.loads((r/'evidence/payload-manifest.json').read_text())[0]
f=r/'inputs/adbd-corrupt.apex';assert not f.exists(),'Preserve existing fixture'
b=bytearray((r/'inputs/adbd.apex').read_bytes());b[p['offset']+100]^=1;f.write_bytes(b)
x=s.run(['/usr/sbin/debugfs','-w','-R',f'write {f} adbd-corrupt.apex',str(r/'artifacts/data-base.ext4')],stdout=s.PIPE,stderr=s.STDOUT,text=True)
(r/'evidence/corrupt-fixture.txt').write_text(x.stdout+f'\nexit={x.returncode}\n');assert x.returncode==0
(r/'evidence/corrupt-fixture.json').write_text(json.dumps({'original_sha256':p['apex_sha256'],'corrupt_sha256':hashlib.sha256(b).hexdigest(),'flipped_byte':p['offset']+100,'xor':1,'purpose':'EIO from dm-verity reading changed first data block; original AVB root unchanged'},indent=2)+'\n')
