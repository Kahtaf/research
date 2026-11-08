from pathlib import Path
import base64,hashlib,json
K=Path('/srv/android/asus-linux49-calibrated-entry-build-20261107/kernel')
paths=['drivers/power/supply/mediatek/battery/Kconfig','drivers/power/supply/mediatek/battery/Makefile','drivers/misc/mediatek/thermal/Kconfig','drivers/misc/mediatek/thermal/Makefile','drivers/misc/mediatek/thermal/mt8163/Makefile','drivers/misc/mediatek/thermal/common/coolers/Makefile','drivers/thermal/Kconfig','drivers/thermal/Makefile','drivers/misc/mediatek/base/Makefile','drivers/misc/mediatek/base/power/Makefile','drivers/misc/mediatek/base/power/mt8163/Makefile','drivers/misc/mediatek/base/power/cpufreq_v1/Makefile','drivers/cpufreq/Makefile','drivers/cpufreq/Kconfig','drivers/misc/mediatek/power/mt8163/asus_p00a/battery_diag.c','drivers/misc/mediatek/power/mt8163/asus_p00a/bq25896.c','drivers/power/supply/mediatek/battery/battery_common.c','drivers/power/supply/mediatek/battery/battery_meter.c','arch/arm64/kernel/asus_retained_trace.c','arch/arm64/kernel/asus_entry_text.S','arch/arm64/kernel/asus_entry_tag.h','arch/arm64/kernel/head.S','drivers/watchdog/mtk_wdt.c']
files={};missing=[]
for n in paths:
 p=K/n
 if p.is_file():
  b=p.read_bytes();files['source/baseline/'+n]=dict(data=base64.b64encode(b).decode(),sha256=hashlib.sha256(b).hexdigest())
 else:missing.append(n)
listing={n:[str(p.relative_to(K)) for p in (K/n).glob('*') if p.is_file()] for n in ['drivers/misc/mediatek/thermal/mt8163','drivers/misc/mediatek/base/power/mt8163','drivers/misc/mediatek/power/mt8163']}
print(json.dumps(dict(files=files,pins={n:v['sha256'] for n,v in files.items()},missing=missing,listing=listing)))
