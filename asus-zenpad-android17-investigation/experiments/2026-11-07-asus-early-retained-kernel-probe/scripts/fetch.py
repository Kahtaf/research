from pathlib import Path
import sys,json,subprocess,hashlib
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parent/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run,SSH
remote=Path('/srv/android/asus-early-retained-kernel-probe-20261107')
script='''from pathlib import Path
import json,hashlib
R=Path('/srv/android/asus-early-retained-kernel-probe-20261107');E=R/'evidence';O=R/'out'
status=json.loads((E/'build-status.json').read_text());assert status['status']=='complete' and status['compile_exit']==0,status
log=(E/'Image.gz-dtb.log').read_bytes();lines=log.decode(errors='replace').splitlines()
names=['asus_retained_trace_early_init','asus_retained_trace_init','asus_retained_trace_write','mtk_timer_init']
maplines=(O/'System.map').read_text().splitlines();symbols={n:[l for l in maplines if l.split()[-1]==n] for n in names}
assert all(symbols.values()),symbols
summary=dict(full_log_remote=str(E/'Image.gz-dtb.log'),full_log_bytes=len(log),full_log_sha256=hashlib.sha256(log).hexdigest(),warning_lines=[l for l in lines if 'warning:' in l],warning_count=sum('warning:' in l for l in lines),error_count=sum('error:' in l for l in lines),tail=lines[-18:],selected_linked_symbols=symbols,complete_compile_exit=status['compile_exit'])
(E/'log-summary.json').write_text(json.dumps(summary,indent=2)+'\\n')
files=['build-status.json','build-receipt.json','changed-source-pins.json','original-selected-inputs.json','log-summary.json','early-api-source.json','patch.log','build-job.stdout','build-job.stderr','Image.gz-dtb.log']
result={'evidence/'+n:(E/n).read_text() for n in files}
for n in ['arch/arm64/kernel/asus_retained_trace.c','arch/arm64/kernel/setup.c','include/linux/asus_retained_trace.h']:
 result['source/final/'+n]=(R/'kernel'/n).read_text()
print(json.dumps(result))
'''
contents=json.loads(run(script))
for n,t in contents.items():
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t)
receipt=json.loads((R/'evidence/build-receipt.json').read_text())
for rr,lr,key in [('out/arch/arm64/boot/Image.gz-dtb','artifacts/Image.gz-dtb','arch/arm64/boot/Image.gz-dtb'),('out/.config','artifacts/resolved.config','.config')]:
 with (R/lr).open('wb') as f:subprocess.run(SSH+['cat',str(remote/rr)],stdout=f,check=True)
 p=R/lr;assert dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())==receipt['artifacts'][key]
print(json.dumps(dict(fetched=True,artifacts=receipt['artifacts'],release=receipt['release'])))
