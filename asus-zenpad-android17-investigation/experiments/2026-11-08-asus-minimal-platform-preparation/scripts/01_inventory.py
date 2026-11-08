from pathlib import Path
import base64,hashlib,json,subprocess
B=Path('/srv/android/asus-linux49-calibrated-entry-build-20261107');K=B/'kernel';O=B/'out'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(O/'.config')=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
assert sha(O/'arch/arm64/boot/Image.gz-dtb')=='97b7e1199d607f852bf52ff7766e8aa079fee92986cd3d473b765a45adbf45fb'
paths=['arch/arm64/boot/dts/mediatek/asus-p00a.dts','arch/arm64/boot/dts/mediatek/mt8163.dtsi','drivers/misc/mediatek/Kconfig','drivers/misc/mediatek/Makefile','drivers/power/supply/mediatek/Kconfig','drivers/power/supply/mediatek/Makefile','drivers/misc/mediatek/power/mt8163/Makefile','drivers/misc/mediatek/power/mt8163/asus_p00a/Makefile','drivers/thermal/mediatek/Makefile','drivers/thermal/mediatek/Kconfig','arch/arm64/kernel/Makefile','include/linux/asus_retained_trace.h','kernel/printk/printk.c']
files={}
for n in paths:
 p=K/n
 if p.is_file():files['source/baseline/'+n]=dict(data=base64.b64encode(p.read_bytes()).decode(),sha256=sha(p))
pattern='ASUS_P00A_BATTERY|ASUS_P00A_MAIN_BATTERY|ASUS_P00A_BQ|THRMAL_ASUS|THERMAL_ASUS|MTK_THERMAL|VIRTUAL_SENSOR_THERMAL|MTK_BASE_POWER|MTK_SMART_BATTERY'
import os,re
lines=[]
for parent,ds,ns in os.walk(K/'drivers'):
 for name in ns:
  if name=='Makefile' or name.startswith('Kconfig'):
   p=Path(parent)/name
   for i,line in enumerate(p.read_text(errors='replace').splitlines(),1):
    if re.search(pattern,line):lines.append(str(p.relative_to(K))+':'+str(i)+':'+line)
print(json.dumps(dict(files=files,git_metadata_present=(K/'.git').exists(),source_identity='receipt-bound independent source tree; no git metadata',declarations=lines,pins={n:v['sha256'] for n,v in files.items()})))
