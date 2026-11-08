from pathlib import Path
import json,re,subprocess
R=Path('/srv/android/asus-sparse-observer-liveness-20261108-e6799dac')
p=R/'out/arch/arm64/kernel/asus_retained_trace.o'
assert b'ASUS49-MODE run=e6799dac-43cb-4222-8ab6-5119397460b6' in p.read_bytes()
d=subprocess.check_output(['aarch64-linux-gnu-objdump','-dr',str(p)],text=True)
n=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(p)],text=True)
print(json.dumps(dict(nm=n,store_release_count=len(re.findall(r'\bstlr\b',d)),writer=d[d.index('<asus_retained_trace_write>:'):d.index('<asus_retained_trace_write>:')+15000])))
