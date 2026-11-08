from pathlib import Path
import json,hashlib,base64,os,subprocess
from vm import R,channel
info=json.loads((R/'evidence/identity.json').read_text())
script='''from pathlib import Path
import json,hashlib,base64,os
B=Path(BASE)
assert B.is_dir() and (B/'kernel').is_dir() and (B/'out').is_dir()
files=['drivers/power/supply/power_supply_core.c','include/linux/power_supply.h','drivers/power/supply/power_supply_leds.c','drivers/power/supply/power_supply_sysfs.c','arch/arm64/kernel/asus_retained_trace.c','include/linux/asus_retained_trace.h','arch/arm64/kernel/asus_entry_tag.h','kernel/workqueue.c']
print(json.dumps(dict(base=str(B),realpath=str(B.resolve()),source_link=str((B/'out/source').resolve()),files={n:dict(sha256=hashlib.sha256((B/'kernel'/n).read_bytes()).hexdigest(),data=base64.b64encode((B/'kernel'/n).read_bytes()).decode(),inode=(B/'kernel'/n).stat().st_ino) for n in files},config_sha256=hashlib.sha256((B/'out/.config').read_bytes()).hexdigest(),image_sha256=hashlib.sha256((B/'out/arch/arm64/boot/Image.gz-dtb').read_bytes()).hexdigest())))
'''.replace('BASE',repr(info['base_remote_root']))
os.chdir(R)
p=subprocess.run(channel()+['python3 -B -'],input=script,text=True,capture_output=True);p.check_returncode();d=json.loads(p.stdout)
assert d['source_link']==info['base_remote_root']+'/kernel'
assert d['config_sha256']==info['config_sha256'] and d['image_sha256']==info['base_compiled_sha256']
for n,v in d.pop('files').items():
 data=base64.b64decode(v['data']);assert hashlib.sha256(data).hexdigest()==v['sha256'];p=R/'source/base'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
(R/'evidence/actual-base.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
