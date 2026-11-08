from pathlib import Path
import json,base64,hashlib,stat
O=Path('/srv/android/asus-final-bpf-runtime-20261106');out={}
for p in list((O/'evidence').glob('*'))+list(O.glob('run-*/*')):
 if p.is_file() and p.name not in ['initramfs.cpio.gz'] and p.stat().st_size<2000000:out[str(p.relative_to(O))]=base64.b64encode(p.read_bytes()).decode()
print(json.dumps(out))
