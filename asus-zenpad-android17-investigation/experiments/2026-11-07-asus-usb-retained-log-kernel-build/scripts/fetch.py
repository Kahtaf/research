from pathlib import Path
import sys,json,subprocess,hashlib
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parent/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run,SSH
remote=Path('/srv/android/asus-usb-retained-log-kernel-build-20261107')
script='''from pathlib import Path
import json,hashlib
R=Path('/srv/android/asus-usb-retained-log-kernel-build-20261107');E=R/'evidence'
status=json.loads((E/'build-status.json').read_text());assert status['status']=='complete' and status['compile_exit']==0,status
log=(E/'Image.gz-dtb.log').read_bytes();lines=log.decode(errors='replace').splitlines()
summary=dict(full_log_remote=str(E/'Image.gz-dtb.log'),full_log_bytes=len(log),full_log_sha256=hashlib.sha256(log).hexdigest(),warning_count=sum('warning:' in l for l in lines),error_count=sum('error:' in l for l in lines),tail=lines[-16:],compile_exit=status['compile_exit'])
(E/'log-summary.json').write_text(json.dumps(summary,indent=2)+'\\n')
files=['build-status.json','build-receipt.json','changed-source-pins.json','original-selected-inputs.json','log-summary.json','patch.log','build-job.stdout','build-job.stderr','launch.json']
result={'evidence/'+n:(E/n).read_text() for n in files}
result['source/final/arch/arm64/kernel/asus_retained_trace.c']=(R/'kernel/arch/arm64/kernel/asus_retained_trace.c').read_text()
print(json.dumps(result))
'''
contents=json.loads(run(script))
for n,t in contents.items():
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t)
receipt=json.loads((R/'evidence/build-receipt.json').read_text())
for rr,lr,key in [('out/arch/arm64/boot/Image.gz-dtb','artifacts/Image.gz-dtb','arch/arm64/boot/Image.gz-dtb'),('out/.config','artifacts/resolved.config','.config')]:
 with (R/lr).open('xb') as f:subprocess.run(SSH+['cat',str(remote/rr)],stdout=f,check=True)
 p=R/lr;assert dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())==receipt['artifacts'][key]
print(json.dumps(dict(fetched=True,artifacts=receipt['artifacts'])))
