#!/usr/bin/env python3
from pathlib import Path
import re,subprocess
k=Path('/srv/android/asus-android17/kernel-bpf-fd')
b=Path('/srv/android/asus-build-integration/compile-fix-before');b.mkdir(exist_ok=False)
files=['drivers/misc/mediatek/include/mt-plat/battery_meter.h','drivers/power/supply/mediatek/battery/asus_p00a_soc.inc','drivers/power/supply/mediatek/battery/battery_meter.c','drivers/misc/mediatek/thermal/mt8163/mtk_ts_battery.c']
for name in files:
 p=k/name;s=p.read_text();old=s
 if name.endswith('battery_meter.h'):
  s=s.replace('#define CUST_CAPACITY_OCV2CV_TRANSFORM','#ifndef CONFIG_ASUS_P00A_MAIN_BATTERY_SOC\n#define CUST_CAPACITY_OCV2CV_TRANSFORM\n#endif')
 elif name.endswith('asus_p00a_soc.inc'):
  s=re.sub(r'\bcurrent\b','model_current',s)
 elif name.endswith('battery_meter.c'):
  start=s.index('static void __batt_meter_parse_multi_battery_data(')
  end=s.index('\n}',start)+2
  s=s[:start]+'#ifdef CONFIG_MTK_MULTI_BAT_PROFILE_SUPPORT\n'+s[start:end]+'\n#endif'+s[end:]
  s=s.replace('signed int battery_meter_get_battery_temperature(void)\n{\n\tsigned int batt_temp = 0;','signed int battery_meter_get_battery_temperature(void)\n{\n#ifdef CONFIG_MTK_BATTERY_LIFETIME_DATA_SUPPORT\n\tsigned int batt_temp = 0;\n#endif')
 else:
  s=s.replace('static int polling_trip_temp_high = 50000;','#ifndef CONFIG_ASUS_P00A_MAIN_BATTERY_SOC\nstatic int polling_trip_temp_high = 50000;\n#endif')
 assert s!=old,name
 copy=b/name;copy.parent.mkdir(parents=True,exist_ok=True);copy.write_text(old);p.write_text(s)
with Path('/srv/android/asus-build-integration/logs/kernel-compile-fix.patch').open('w') as f:
 for name in files:
  r=subprocess.run(['diff','-u','--label','a/'+name,'--label','b/'+name,str(b/name),str(k/name)],stdout=f)
  assert r.returncode==1
