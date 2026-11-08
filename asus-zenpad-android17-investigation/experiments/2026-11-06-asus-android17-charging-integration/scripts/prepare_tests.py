#!/usr/bin/env python3
from pathlib import Path
import re,shutil,json,hashlib
R=Path(__file__).resolve().parents[1];S=R/'staged';B=R/'source/kernel-after-soc';I=R/'evidence/host/include';I.mkdir(parents=True,exist_ok=True)
def function(s,name):
 m=re.search(r'\b'+re.escape(name)+r'\([^;{}]*\)\s*\{',s);assert m,name
 start=s.rfind('\n',0,m.start())+1;b=s.index('{',m.start());i=b+1;depth=1
 while depth:
  if s[i]=='{':depth+=1
  elif s[i]=='}':depth-=1
  i+=1
 return s[start:i]
s=(S/'drivers/misc/mediatek/power/mt8163/asus_p00a/bq25896.c').read_text()
(I/'driver_types.h').write_text(s[s.index('#define REG_INPUT'):s.index('bool chargin_hw_init_done;')])
(I/'driver_entrypoints.h').write_text('\n'.join(function(s,n) for n in ['chr_control_interface','p00a_next_poll','p00a_suspend','p00a_resume','p00a_remove','p00a_shutdown']))
for path in ['linux','linux/power','mt-plat','mach']:(I/path).mkdir(exist_ok=True)
s=(B/'include/linux/power_supply.h').read_text();(I/'linux/power_supply.h').write_text('#pragma once\n#include <stdint.h>\ntypedef int64_t s64;\n'+s[s.index('enum {'):s.index('struct device_node;')])
(I/'linux/errno.h').write_text('#include <errno.h>\n')
(I/'linux/kernel.h').write_text('#ifndef ARRAY_SIZE\n#define ARRAY_SIZE(a) (sizeof(a)/sizeof((a)[0]))\n#endif\n')
shutil.copy(B/'drivers/misc/mediatek/include/mt-plat/mt8163/include/mach/upmu_hw.h',I/'mach/upmu_hw.h')
shutil.copy(R/'source/test-fixtures/platform_enums.h',I/'platform_enums.h')
(I/'mt-plat/charging.h').write_text('#include "platform_enums.h"\n')
for n in ['model_types.h','dt_properties.h','model_functions.h','reference_asus.h','reference_recurrence.h']:
 shutil.copy(R/'source/test-fixtures'/n,I/n)
shutil.copy(B/'drivers/misc/mediatek/include/mt-plat/battery_meter_table.h',I/'mt-plat/battery_meter_table.h')
s=(B/'drivers/power/supply/mediatek/battery/battery_meter.c').read_text()
parts=[function(s,n) for n in ['oam_init','oam_run','battery_meter_get_battery_percentage','battery_meter_initial','battery_meter_reset','reset_parameter_car','reset_parameter_dod_change','reset_parameter_dod_full','battery_meter_suspend','battery_meter_resume']]
s=(S/'drivers/power/supply/mediatek/battery/battery_common.c').read_text();parts += [function(s,'BAT_thread'),function(s,'check_battery_exist')]
s=(B/'drivers/misc/mediatek/thermal/mt8163/mtk_ts_battery.c').read_text();parts.append(function(s,'mtktsbattery_get_temp'))
(I/'kernel_entrypoints.h').write_text('\n'.join(parts)+'\n')
manifest={str(p.relative_to(I)):hashlib.sha256(p.read_bytes()).hexdigest() for p in I.rglob('*') if p.is_file()}
(R/'evidence/host-extraction.json').write_text(json.dumps(manifest,indent=2)+'\n')
