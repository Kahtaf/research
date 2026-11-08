from pathlib import Path
import base64,hashlib,json
K=Path('/srv/android/asus-linux49-calibrated-entry-build-20261107/kernel')
paths=['drivers/misc/mediatek/thermal/mt8163/mtk_ts_cpu.c','drivers/misc/mediatek/thermal/mt8163/mtk_ts_battery.c','drivers/misc/mediatek/thermal/mt8163/mtk_ts_pmic6323.c','drivers/misc/mediatek/base/power/mt8163/mt_cpufreq.c','drivers/misc/mediatek/power/mt8163/asus_p00a/control.h','drivers/misc/mediatek/base/power/Kconfig','drivers/misc/mediatek/base/power/hps_v1/Makefile','drivers/misc/mediatek/gpu/Kconfig','drivers/misc/mediatek/video/Kconfig','drivers/misc/mediatek/lcm/Kconfig','drivers/misc/mediatek/usb20/Kconfig','drivers/misc/mediatek/usb11/Kconfig','drivers/misc/mediatek/cameraisp/Kconfig','drivers/misc/mediatek/sensors-1.0/Kconfig','drivers/cpuidle/Kconfig','arch/arm64/Kconfig','drivers/misc/mediatek/power/mt8163/asus_p00a/charge_snapshot.inc','drivers/misc/mediatek/thermal/common/coolers/mtk_cooler_shutdown.c']
files={};missing=[]
for n in paths:
 p=K/n
 if p.is_file():
  b=p.read_bytes();files['source/baseline/'+n]=dict(data=base64.b64encode(b).decode(),sha256=hashlib.sha256(b).hexdigest())
 else:missing.append(n)
print(json.dumps(dict(files=files,pins={n:v['sha256'] for n,v in files.items()},missing=missing)))
