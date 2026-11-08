#!/usr/bin/env python3
import io,pathlib,subprocess,tarfile,sys,json,hashlib
from remote import SSH
r=pathlib.Path(__file__).resolve().parents[1]
cmd='cd /srv/android/asus-radio-kernel-port && tar -czf - logs build/.config build/System.map build/arch/arm64/boot/Image.gz-dtb build/drivers/misc/mediatek/connectivity/built-in.o userspace/bin/p00a-wmt-arm64'
p=subprocess.run(SSH+[cmd],check=True,stdout=subprocess.PIPE)
d=r/'evidence/linux-build';d.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(p.stdout),mode='r:gz') as t:t.extractall(d,filter='data')
manifest={str(p.relative_to(d)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(d.rglob('*')) if p.is_file()}
(r/'evidence/linux-build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Captured',len(manifest),'compiler outputs/logs; archive bytes',len(p.stdout))
