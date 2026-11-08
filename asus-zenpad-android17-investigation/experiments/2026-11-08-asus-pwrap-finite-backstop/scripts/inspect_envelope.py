from pathlib import Path
import base64,hashlib,json,subprocess
from vm import R,channel
s='''from pathlib import Path
import base64,hashlib,json,subprocess
B=Path('/srv/android/asus-devkmsg-return-boundary-20261108-e7acab50');K=B/'kernel';O=B/'out'
files={}
for n in ['drivers/soc/mediatek/mtk-pmic-wrap.c','arch/arm64/boot/dts/mediatek/mt8163.dtsi','drivers/cpufreq/Makefile','drivers/cpufreq/Kconfig','drivers/clk/mediatek/clk-mt8163.c']:
 p=K/n
 if p.exists():files['source/'+n]=base64.b64encode(p.read_bytes()).decode()
for sym in ['pwrap_read','pwrap_write','pwrap_readl.isra.0','sched_clock']:
 files['evidence/elf/'+sym+'.disasm']=base64.b64encode(subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--disassemble='+sym,str(O/'vmlinux')])).decode()
config=(O/'.config').read_bytes()
print(json.dumps(dict(files=files,config_sha256=hashlib.sha256(config).hexdigest(),config_selected=[l for l in config.decode().splitlines() if any(x in l for x in ['CPU_FREQ','CPUFREQ','MTK_CLK','MTK_DVFS','MACH_MT8163'])],frequency_names=subprocess.check_output(['find',str(K/'drivers/cpufreq'),str(K/'drivers/misc/mediatek'),'dict-placeholder'],stderr=subprocess.DEVNULL,text=True) if False else subprocess.check_output(['bash','-c',"find drivers/cpufreq drivers/misc/mediatek -maxdepth 4 -type f \\( -iname '*cpufreq*' -o -iname '*dvfs*' -o -iname '*freq*' \\)"],cwd=K,text=True).splitlines())))
'''
p=subprocess.run(channel()+['python3 -B -'],input=s,text=True,capture_output=True,timeout=60)
(R/'evidence/envelope-inspection.stderr').write_text(p.stderr);p.check_returncode();d=json.loads(p.stdout)
for n,v in d.pop('files').items():
 b=base64.b64decode(v);p=R/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);d.setdefault('files',{})[n]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
assert d['config_sha256']=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
(R/'evidence/envelope-inspection.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
