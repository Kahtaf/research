#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];rev='717bb3c9e13ce573cfdd2dda856debd27a0fa17f'
ssh=json.loads((R.parent/'2026-11-06-asus-android17-battery-gauge/evidence/remote-source.json').read_text())['ssh']
files=['Makefile','drivers/misc/mediatek/power/mt8163/asus_p00a/policy.h','drivers/misc/mediatek/include/mt-plat/battery_common.h','drivers/misc/mediatek/include/mt-plat/battery_meter_hal.h','include/linux/of.h','include/linux/timekeeping.h','include/linux/math64.h','include/linux/pm_wakeup.h','drivers/power/supply/power_supply_core.c','drivers/power/supply/power_supply_sysfs.c']
manifest={}
for p in files:
 data=subprocess.check_output(ssh+['git -C /srv/android/asus-android17/kernel-bpf-fd show '+rev+':'+p]);f=R/'source/kernel-base'/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data);manifest[p]=hashlib.sha256(data).hexdigest()
query='git -C /srv/android/asus-android17/kernel-bpf-fd grep -n -E "(battery_meter_get_battery_percentage|battery_meter_initial|battery_meter_reset|battery_meter_get_battery_soc|battery_meter_get_battery_temperature|force_get_tbat|fgauge_read_d_by_v|fgauge_construct_battery_profile|mt_battery_GetBatteryData|oam_d_|oam_car_)" '+rev+' -- drivers include'
data=subprocess.check_output(ssh+[query]);(R/'evidence/kernel-callers-complete.txt').write_bytes(data)
(R/'evidence/kernel-additional-source.json').write_text(json.dumps({'revision':rev,'sha256':manifest,'caller_search':query},indent=2)+'\n')
print('Fetched',len(files),'source files and pinned caller search; read-only.')
