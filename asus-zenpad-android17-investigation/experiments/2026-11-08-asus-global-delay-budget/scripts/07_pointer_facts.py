from pathlib import Path
import base64,hashlib,json
K=Path('/srv/android/asus-global-delay-budget-20261108/kernel');files={}
for n in ['lib/vsprintf.c','arch/arm64/kernel/traps.c','lib/dump_stack.c']:
 d=(K/n).read_bytes();files['source/ancestor/'+n]=dict(data=base64.b64encode(d).decode(),sha256=hashlib.sha256(d).hexdigest())
print(json.dumps(dict(files=files)))
