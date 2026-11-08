from pathlib import Path
import subprocess,json,hashlib
R=Path('/srv/android/asus-final-image-startup-20261107');raw=Path('/srv/android/asus-radio-trigger-build-r4/system-partition.raw');rows=[]
for n,p in [('aconfigd.rc','/system/etc/init/aconfigd.rc'),('odsign.rc','/system/etc/init/odsign.rc'),('init.mt8163.rc','/system/vendor/etc/init/hw/init.mt8163.rc')]:
 x=subprocess.run(['/usr/sbin/debugfs','-R','cat '+p,str(raw)],capture_output=True,timeout=10)
 if x.stdout:(R/'evidence'/('final-'+n)).write_bytes(x.stdout);rows.append(dict(path=p,bytes=len(x.stdout),sha256=hashlib.sha256(x.stdout).hexdigest()));print(p);print(x.stdout.decode())
(R/'evidence/selected-init-source-pins.json').write_text(json.dumps(rows,indent=2))
