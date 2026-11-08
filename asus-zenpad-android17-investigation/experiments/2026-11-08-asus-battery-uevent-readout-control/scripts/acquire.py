from pathlib import Path
import base64,json,subprocess
from vm import R,channel
s='''from pathlib import Path
import base64,json,hashlib,gzip
B=Path('/srv/android/asus-pwrap-finite-backstop-20261108-09abbded');K=B/'kernel';O=B/'out'
names=['drivers/power/supply/power_supply_core.c','drivers/power/supply/power_supply_sysfs.c','drivers/power/supply/mediatek/battery/battery_common.c','drivers/misc/mediatek/power/mt8163/asus_p00a/battery_diag.c','drivers/power/supply/mediatek/battery/battery_meter.c']
plumbing=['arch/arm64/kernel/asus_retained_trace.c','arch/arm64/kernel/asus_entry_tag.h','include/linux/asus_retained_trace.h']
files={n:base64.b64encode((K/n).read_bytes()).decode() for n in names+plumbing}
files['evidence/base.config']=base64.b64encode((O/'.config').read_bytes()).decode()
m=(O/'System.map').read_bytes();files['evidence/base-System.map.gz']=base64.b64encode(gzip.compress(m,mtime=0)).decode()
dirs=['drivers/misc/mediatek/power/mt8163/asus_p00a','drivers/power/supply/mediatek']
print(json.dumps(dict(files=files,source_pins={n:hashlib.sha256((K/n).read_bytes()).hexdigest() for n in names+plumbing},inventory_names=names,scoped_filenames={n:[str(p.relative_to(K)) for p in (K/n).iterdir()] for n in dirs},vmlinux_sha256=hashlib.sha256((O/'vmlinux').read_bytes()).hexdigest(),config_sha256=hashlib.sha256((O/'.config').read_bytes()).hexdigest(),map_sha256=hashlib.sha256(m).hexdigest())))
'''
p=subprocess.run(channel()+['python3 -B -'],input=s,text=True,capture_output=True,timeout=60);(R/'evidence/acquire.stderr').write_text(p.stderr);p.check_returncode();d=json.loads(p.stdout)
for n,v in d.pop('files').items():
 p=R/n if n.startswith('evidence/') else R/'source/base'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(v))
assert d['vmlinux_sha256']=='bd8f6a2aa30ca56726bbad38399e7086125396caafa8c4b15298c854e1d4c667'
assert d['config_sha256']=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
(R/'evidence/acquisition.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d['scoped_filenames'],indent=2))
