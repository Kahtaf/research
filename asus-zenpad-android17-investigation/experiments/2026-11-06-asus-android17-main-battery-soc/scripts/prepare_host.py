#!/usr/bin/env python3
from pathlib import Path
import re,json,hashlib,shutil
R=Path(__file__).resolve().parents[1];O=R/'evidence/host';I=O/'include';I.mkdir(parents=True,exist_ok=True)
# Do not import staging script: it performs mutations. Extract exact definitions.
def function(s,name):
 m=re.search(r'\b'+re.escape(name)+r'\([^;{}]*\)\s*\{',s);assert m,name
 start=s.rfind('\n',0,m.start())+1;b=s.index('{',m.start());i=b+1;depth=1
 while depth:
  if s[i]=='{':depth+=1
  elif s[i]=='}':depth-=1
  i+=1
 return s[start:i]
base=R/'source/kernel-after-measurement';st=R/'staged'
text=(base/'include/linux/power_supply.h').read_text();part=text[text.index('enum {'):text.index('struct device_node;')]
(I/'linux').mkdir(exist_ok=True)
(I/'linux/power_supply.h').write_text('#pragma once\n#include <stdint.h>\n'+part)
(I/'linux/errno.h').write_text('#include <errno.h>\n')
(I/'linux/kernel.h').write_text('#ifndef ARRAY_SIZE\n#define ARRAY_SIZE(a) (sizeof(a)/sizeof((a)[0]))\n#endif\n')
(I/'mach').mkdir(exist_ok=True)
shutil.copy(base/'drivers/misc/mediatek/include/mt-plat/mt8163/include/mach/upmu_hw.h',I/'mach/upmu_hw.h')
s=(st/'drivers/power/supply/mediatek/battery/battery_meter.c').read_text()
names=['fgauge_get_saddles','fgauge_get_saddles_r_table','fgauge_get_profile','fgauge_get_profile_r_table','fgauge_get_Q_max','fgauge_get_Q_max_high_current','fgauge_construct_battery_profile','fgauge_construct_r_table_profile','fgauge_read_capacity_by_v','fgauge_read_d_by_v','fgauge_read_v_by_d','fgauge_read_v_by_capacity','fgauge_read_r_bat_by_v','__batt_meter_parse_table']
parts={n:function(s,n) for n in names}
# Emit the exact source macros too, so selectors cannot diverge in tests.
macro=s[s.index('#ifdef CONFIG_ASUS_P00A_MAIN_BATTERY_SOC\n#define P00A_LOW_T2'):s.index('signed int fgauge_get_Q_max(signed short temperature)')]
fields=sorted(set(re.findall(r'batt_meter_cust_data\.(\w+)',s)))
(I/'model_types.h').write_text('struct battery_meter_custom_data {\n'+''.join(' int '+f+';\n' for f in fields)+'} batt_meter_cust_data;\n')
(I/'model_functions.h').write_text(macro+'\n'.join(parts.values()))
# Actual DT source, not a separate toy battery fit.
dt=(base/'arch/arm64/boot/dts/mediatek/asus8163_tb_380_m_bat_setting.dtsi').read_text();dt=re.sub(r'/\*.*?\*/','',dt,flags=re.S)
props={}
for name,raw in re.findall(r'\b(\w+)\s*=\s*<([^>]+)>',dt):
 vals=[int(x.strip('()'),0) for x in raw.split()];props[name]=vals
h='static struct property properties[] = {\n'
for k,vals in props.items():h+=' {"'+k+'", '+str(len(vals))+', {'+','.join(map(str,vals))+'}},\n'
h+='};\nstatic void load_fields(void) {\n u32 value;\n'
for f in fields:h+=f' if (!of_property_read_u32(&node,"{f}",&value)) batt_meter_cust_data.{f}=value;\n'
h+='}\n';(I/'dt_properties.h').write_text(h)
# Independent source-revision oracle: original ASUS four-axis constructors/Qmax.
orig=(R/'source/asus-3.18/drivers/power/mediatek/battery_meter.c').read_text()
refnames=['fgauge_get_Q_max','fgauge_get_Q_max_high_current','fgauge_construct_battery_profile','fgauge_construct_r_table_profile','fgauge_read_d_by_v','fgauge_read_v_by_d','fgauge_read_r_bat_by_v']
ref=''
for n in refnames:
 source=orig
 if n.startswith('fgauge_get_Q_max'):
  first=function(orig,n);source=orig[orig.index(first)+len(first):]
 t=function(source,n)
 t=re.sub(r'\b'+n+r'\b','reference_'+n,t)
 ref+=t+'\n'
(I/'reference_asus.h').write_text(ref)
# Extract the independent D2 recurrence statements directly from stock source.
oam=function(orig,'oam_run')
segments=[]
for var in ['oam_i_2','oam_car_2','oam_d_2','oam_v_ocv_2','oam_r_2']:
 m=re.search(r'\b'+var+r' = [^;]+;',oam);assert m,var;segments.append(m.group(0))
(I/'reference_recurrence.h').write_text('\n'.join(segments[:3])+'''\nif (oam_d_2 < 0) oam_d_2 = 0;
if (oam_d_2 > 100) oam_d_2 = 100;
'''+ '\n'.join(segments[3:])+'\n')
manifest={'extracted_functions':{n:hashlib.sha256(t.encode()).hexdigest() for n,t in parts.items()},'original_functions':refnames,'dt_sha256':hashlib.sha256((base/'arch/arm64/boot/dts/mediatek/asus8163_tb_380_m_bat_setting.dtsi').read_bytes()).hexdigest()}
(R/'evidence/host-extraction.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Previous exact ADC/status test is copied and extended; original stays untouched.
old=(R.parent/'2026-11-06-asus-android17-battery-gauge/tests/host_battery.c').read_text()
old=old.replace('#include "pmic_battery.inc"','''#include <linux/power/asus_p00a_battery.h>
static int invalidations;
void asus_p00a_soc_invalidate(int error) { CHECK(error < 0); invalidations++; }
int asus_p00a_soc_capacity(int *capacity) { (void)capacity; return -ENODATA; }
#include "pmic_battery.inc"''')
old=old.replace('CHECK(reg == AUXADC_CON11 || reg == AUXADC_CON22 || reg == AUXADC_CON19);','''CHECK(reg == AUXADC_CON11 || reg == AUXADC_CON22 || reg == AUXADC_CON19 ||
 (reg == CHR_CON7 && val == 1 && mask == 1 &&
  (shift == PMIC_BATON_TDET_EN_SHIFT || shift == PMIC_RG_BATON_EN_SHIFT)));''')
old=old.replace('\tprintf("PASS:', '''
 reset(); regs[CHR_CON7]=0;
 CHECK(asus_p00a_pmic_enable_baton()==0);
 CHECK(writes==2 && wake_count==0 && pmic_adc_mutex.locked==0);
 CHECK(regs[CHR_CON7]==(BIT(PMIC_RG_BATON_EN_SHIFT)|BIT(PMIC_BATON_TDET_EN_SHIFT)));
 for(i=1;i<=3;i++) {
  reset(); regs[CHR_CON7]=0; fail_operation=i;
  CHECK(asus_p00a_pmic_enable_baton()==-EIO);
  CHECK(wake_count==0 && pmic_adc_mutex.locked==0);
 }
 reset(); pwrap_regmap=NULL;CHECK(asus_p00a_pmic_enable_baton()==-ENODATA);
 CHECK(invalidations>0);
\tprintf("PASS:''',1)
(O/'host_measurement.c').write_text(old)
print('Prepared exact production extracts, original ASUS oracle and extended transport harness.')
health=(R/'integration/platform/hardware/interfaces/health/aidl/default/Health.cpp').read_text()
loop=(R/'integration/platform/hardware/interfaces/health/aidl/default/HalHealthLoop.cpp').read_text()
# The ordinary extractor begins at the line containing Class::method.
def method(s,name):
 m=re.search(r'\b'+re.escape(name)+r'\([^;{}]*\)\s*\{',s);assert m,name
 a=s.rfind('\n',0,m.start())+1;b=s.index('{',m.start());i=b+1;depth=1
 while depth:
  if s[i]=='{':depth+=1
  elif s[i]=='}':depth-=1
  i+=1
 return s[a:i]
parts=[method(health,'Health::'+n) for n in ['getHealthInfo','ReadBatterySnapshot','registerCallback','update','OnHealthInfoChanged']]
parts += [method(loop,'HalHealthLoop::'+n) for n in ['ScheduleBatteryUpdate','OnHealthInfoChanged','set_charger_online']]
board=(R/'integration/device/asus/p00a/health/Health.cpp').read_text()
# inline override has a trailing 'override' before its brace.
board=board.replace('ReadBatterySnapshot(HealthInfo* out) override','P00aHealth::ReadBatterySnapshot(HealthInfo* out)')
parts.append(method(board,'P00aHealth::ReadBatterySnapshot'))
(I/'health_functions.h').write_text('\n\n'.join(parts)+'\n')
(R/'evidence/health-host-extraction.json').write_text(json.dumps({'sha256':[hashlib.sha256(t.encode()).hexdigest() for t in parts],'scope':'exact staged methods, binder/monitor primitives simulated'},indent=2)+'\n')
# Compile and exercise the actual integration entry points, not just the core.
s=(st/'drivers/power/supply/mediatek/battery/battery_meter.c').read_text()
wrappers=[function(s,n) for n in ['oam_init','oam_run','battery_meter_get_battery_percentage','battery_meter_initial','battery_meter_reset','reset_parameter_car','reset_parameter_dod_change','reset_parameter_dod_full','battery_meter_suspend','battery_meter_resume']]
s=(st/'drivers/power/supply/mediatek/battery/battery_common.c').read_text()
wrappers += [function(s,'BAT_thread'),function(s,'check_battery_exist')]
s=(st/'drivers/misc/mediatek/thermal/mt8163/mtk_ts_battery.c').read_text();wrappers.append(function(s,'mtktsbattery_get_temp'))
(I/'kernel_entrypoints.h').write_text('\n\n'.join(wrappers)+'\n')
