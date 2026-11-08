from pathlib import Path
import json,hashlib,base64
B=Path('/srv/android/asus-linux49-scheduler-switch-capture-20261107-3d26cc95')
files=['kernel/sched/core.c','kernel/workqueue_internal.h','kernel/workqueue.c','kernel/kthread.c','include/linux/kthread.h','include/linux/sched.h','arch/arm64/kernel/asus_retained_trace.c','arch/arm64/kernel/asus_entry_tag.h','include/linux/asus_retained_trace.h','arch/arm64/include/asm/arch_timer.h','arch/arm64/mm/cache.S','arch/arm64/include/asm/current.h','arch/arm64/kernel/asm-offsets.c']
print(json.dumps({n:dict(sha256=hashlib.sha256((B/'kernel'/n).read_bytes()).hexdigest(),data=base64.b64encode((B/'kernel'/n).read_bytes()).decode()) for n in files}))
