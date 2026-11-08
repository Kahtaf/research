from pathlib import Path
import json,base64,hashlib
B=Path('/srv/android/asus-sparse-observer-liveness-20261108-e6799dac')
names=['drivers/watchdog/mediatek/Makefile','drivers/watchdog/mediatek/wdk/Makefile','drivers/watchdog/watchdog_dev.c','kernel/notifier.c','arch/arm64/kernel/process.c']
files={n:(B/'kernel'/n).read_bytes() for n in names}
print(json.dumps({n:dict(sha256=hashlib.sha256(v).hexdigest(),data=base64.b64encode(v).decode()) for n,v in files.items()}))
