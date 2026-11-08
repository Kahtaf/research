from pathlib import Path
import json,hashlib,base64
B=Path('/srv/android/asus-linux49-rdma-registration-skip-20261107-d140b2bf')
files=['kernel/sched/core.c','arch/arm64/kernel/asus_retained_trace.c','arch/arm64/kernel/asus_entry_tag.h','include/linux/asus_retained_trace.h','arch/arm64/include/asm/arch_timer.h','arch/arm64/mm/cache.S']
print(json.dumps({n:dict(sha256=hashlib.sha256((B/'kernel'/n).read_bytes()).hexdigest(),data=base64.b64encode((B/'kernel'/n).read_bytes()).decode()) for n in files}))
