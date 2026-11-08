from pathlib import Path
import base64,json,subprocess
B=Path('/srv/android/asus-linux49-calibrated-entry-build-20261107')
files=['include/linux/asus_retained_trace.h','arch/arm64/kernel/asus_retained_trace.c','arch/arm64/kernel/asus_entry_tag.h','kernel/time/timekeeping.c','drivers/clocksource/arm_arch_timer.c','include/linux/seqlock.h']
print(json.dumps(dict(files={n:base64.b64encode((B/'kernel'/n).read_bytes()).decode() for n in files},jobs=subprocess.run(['ps','-eo','pid,args'],capture_output=True,text=True).stdout,space=subprocess.run(['df','-h','/srv/android'],capture_output=True,text=True).stdout)))
