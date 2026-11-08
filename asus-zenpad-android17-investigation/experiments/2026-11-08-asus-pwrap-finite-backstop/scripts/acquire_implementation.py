from pathlib import Path
import base64,hashlib,json,subprocess
from vm import R,channel
names=['drivers/soc/mediatek/mtk-pmic-wrap.c','include/linux/asus_retained_trace.h','arch/arm64/kernel/asus_retained_trace.c','arch/arm64/kernel/asus_entry_tag.h','drivers/power/supply/mediatek/battery/battery_common.c','drivers/misc/mediatek/power/mt8163/asus_p00a/battery_diag.c','drivers/misc/mediatek/power/mt8163/asus_p00a/pmic_battery.inc','include/linux/atomic.h','include/linux/compiler.h','arch/arm64/include/asm/atomic.h','arch/arm64/include/asm/barrier.h']
s='''from pathlib import Path
import base64,json,hashlib,subprocess
B=Path('/srv/android/asus-devkmsg-return-boundary-20261108-e7acab50');K=B/'kernel';O=B/'out'
names=NAMES
files={n:base64.b64encode((K/n).read_bytes()).decode() for n in names}
files['evidence/base.config']=base64.b64encode((O/'.config').read_bytes()).decode()
print(json.dumps(dict(files=files,source_metadata={n:dict(inode=(K/n).stat().st_ino,mtime_ns=(K/n).stat().st_mtime_ns) for n in names})))
'''.replace('NAMES',repr(names))
p=subprocess.run(channel()+['python3 -B -'],input=s,text=True,capture_output=True,timeout=60);(R/'evidence/implementation-acquisition.stderr').write_text(p.stderr);p.check_returncode();d=json.loads(p.stdout)
for n,v in d.pop('files').items():
 b=base64.b64decode(v);p=R/n if n.startswith('evidence/') else R/'source/base'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);d.setdefault('files',{})[n]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
(R/'evidence/implementation-acquisition.json').write_text(json.dumps(d,indent=2)+'\n');print('Scoped exact implementation inputs saved')
