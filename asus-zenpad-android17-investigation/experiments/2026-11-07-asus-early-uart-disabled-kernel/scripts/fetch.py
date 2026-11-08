from pathlib import Path
import sys,json,subprocess,hashlib
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parent/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run,SSH
remote=Path('/srv/android/asus-early-uart-disabled-kernel-20261107')
s='''from pathlib import Path
import json,hashlib
R=Path('/srv/android/asus-early-uart-disabled-kernel-20261107');E=R/'evidence'
status=json.loads((E/'build-status.json').read_text())
assert status['status'] in ['complete','failed'],'Compile is not finished; no process inspection'
log=(E/'Image.gz-dtb.log').read_bytes();lines=log.decode(errors='replace').splitlines()
summary=dict(full_log_remote=str(E/'Image.gz-dtb.log'),full_log_bytes=len(log),full_log_sha256=hashlib.sha256(log).hexdigest(),warning_count=sum('warning:' in l for l in lines),error_count=sum('error:' in l for l in lines),tail=lines[-16:],compile_exit=status.get('compile_exit'))
(E/'log-summary.json').write_text(json.dumps(summary,indent=2)+'\\n')
files=['prepare-status.json','baseline-selected-pins.json','source-copy.json','config-delta.json','config.diff','dependency-gate.json','build-status.json','build-receipt.json','original-selected-inputs.json','linked-image-assertions.json','log-summary.json','build-job.stdout','build-job.stderr']
result={'evidence/'+n:(E/n).read_text() for n in files if (E/n).exists()}
for n in ['arch/arm64/kernel/asus_retained_trace.c','drivers/tty/serial/8250/Kconfig','drivers/tty/serial/8250/Makefile','arch/arm64/Kconfig']:
 result['source/selected/'+n]=(R/'kernel'/n).read_text()
print(json.dumps(result))
'''
for n,t in json.loads(run(s)).items():
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t)
status=json.loads((R/'evidence/build-status.json').read_text());assert status['status']=='complete' and status['compile_exit']==0,status
receipt=json.loads((R/'evidence/build-receipt.json').read_text())
for rr,lr,key in [('out/arch/arm64/boot/Image.gz-dtb','artifacts/Image.gz-dtb','arch/arm64/boot/Image.gz-dtb'),('out/.config','artifacts/resolved.config','.config')]:
 assert receipt['artifacts'][key]['bytes']<32*1024**2
 with (R/lr).open('xb') as f:subprocess.run(SSH+['cat',str(remote/rr)],stdout=f,check=True)
 p=R/lr;assert dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())==receipt['artifacts'][key]
print(json.dumps(dict(fetched=True,artifacts=receipt['artifacts'])))
