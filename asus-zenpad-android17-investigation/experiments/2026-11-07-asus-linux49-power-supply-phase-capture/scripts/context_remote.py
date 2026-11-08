from pathlib import Path
import json,base64,hashlib
B=Path('/srv/android/asus-linux49-work-dispatch-capture-20261107-b4702f9a/kernel')
print(json.dumps({n:dict(data=base64.b64encode((B/n).read_bytes()).decode(),sha256=hashlib.sha256((B/n).read_bytes()).hexdigest()) for n in ['include/linux/preempt.h','include/linux/hardirq.h']}))
