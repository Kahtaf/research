from pathlib import Path
import json,subprocess,base64,hashlib
from vm import R,channel
s='''from pathlib import Path
import subprocess,json,hashlib,base64
B=Path('/srv/android/asus-devkmsg-return-boundary-20261108-e7acab50');K=B/'kernel';O=B/'out'
names=['drivers/misc/mediatek/base/power/mt8163/mt_cpufreq.c','drivers/misc/mediatek/base/power/mt8163/mt_cpufreq.h','drivers/misc/mediatek/base/power/mt8163/Makefile','drivers/misc/mediatek/base/power/Makefile','drivers/clk/mediatek/clk-pll.c','drivers/clk/mediatek/clk-pll.h']
files={}
for n in names:
 p=K/n
 if p.exists():files[n]=base64.b64encode(p.read_bytes()).decode()
print(json.dumps(dict(files=files,config=[l for l in (O/'.config').read_text().splitlines() if any(x in l for x in ['MT_CPU','MTK_CPU','MTK_DVFS','FREQ_HOP','FREQHOP','MTK_FREQ','MTK_BASE_POWER'])],objects=[dict(name=n,exists=(O/n).exists()) for n in ['drivers/misc/mediatek/base/power/mt8163/mt_cpufreq.o','drivers/clk/mediatek/clk-mt8163.o','drivers/clk/mediatek/clk-pll.o']])) )
'''
p=subprocess.run(channel()+['python3 -B -'],input=s,text=True,capture_output=True,timeout=40);(R/'evidence/frequency.stderr').write_text(p.stderr);p.check_returncode();d=json.loads(p.stdout)
for n,b in d.pop('files').items():
 b=base64.b64decode(b);p=R/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);d.setdefault('files',{})[n]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
(R/'evidence/frequency.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
