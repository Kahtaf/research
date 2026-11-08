#!/usr/bin/env python3
"""Deterministically stage the incremental kernel change; never edits inputs."""
from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
BASE=R/'source/kernel-after-measurement'; OUT=R/'staged'
CFG='CONFIG_ASUS_P00A_MAIN_BATTERY_SOC'
def read(p): return (BASE/p).read_text()
def write(p,s):
 f=OUT/p; f.parent.mkdir(parents=True,exist_ok=True); f.write_text(s)
def fnspan(s,name):
 m=re.search(r'\b'+re.escape(name)+r'\([^;{}]*\)\s*\{',s); assert m,name
 start=s.rfind('\n',0,m.start())+1
 # include multi-line return type (not needed for these functions)
 brace=s.index('{',m.start()); depth=1; i=brace+1
 while depth:
  if s[i]=='{':depth+=1
  elif s[i]=='}':depth-=1
  i+=1
 return start,brace,i
def override(s,name,body):
 a,b,c=fnspan(s,name)
 return s[:b+1]+'\n#ifdef '+CFG+'\n'+body+'\n#else\n'+s[b+1:c-1]+'\n#endif\n'+s[c-1:]
def editfn(s,name,edit):
 a,b,c=fnspan(s,name); return s[:a]+edit(s[a:c])+s[c:]
p='drivers/power/supply/mediatek/battery/battery_meter.c';s=read(p)
s=s.replace('#include <linux/slab.h>','#include <linux/slab.h>\n#include <linux/math64.h>\n#include <linux/power/asus_p00a_battery.h>')
s=s.replace('#define PROFILE_SIZE 5','#ifdef '+CFG+'\n#define PROFILE_SIZE 4\nstatic bool p00a_model_ready;\nstatic int p00a_validate_dt(const struct device_node *np);\n#else\n#define PROFILE_SIZE 5\n#endif')
s=s.replace('\tint addr, val, idx, saddles;', '\tu32 addr, val;\n\tint idx, saddles;', 1)
# Strictly bounded parser: prior loop could write entry 105 into a 104-entry array.
s=s.replace('while (!of_property_read_u32_index(np, node_srting, idx, &addr)) {','while (idx < saddles * 2 &&\n\t       !of_property_read_u32_index(np, node_srting, idx, &addr)) {',1)
s=s.replace('''\t\tif (!of_property_read_u32_index(np, node_srting, idx, &val)) {
\t\t\tpr_debug("batt_temperature_table: addr: %d, val: %d\\n",
\t\t\t\t    addr, val);
\t\t}''','''\t\tif (of_property_read_u32_index(np, node_srting, idx, &val))
\t\t\treturn;''',1)
# Preflight exact DT shapes before this legacy void parser can touch arrays.
anchor='\t__batt_meter_parse_node(np, "vbat_channel_number",'
s=s.replace(anchor,'#ifdef '+CFG+'\n\tif (p00a_validate_dt(np)) {\n\t\tof_node_put(np);\n\t\treturn -EINVAL;\n\t}\n#endif\n\n'+anchor,1)
# The intermediate 10 C axis does not exist on this board. Keep generic boards unchanged.
for name in ['fgauge_get_Q_max','fgauge_get_Q_max_high_current','fgauge_construct_battery_profile','fgauge_construct_r_table_profile']:
 def four(t):
  start=t.index('\t} else if (temperature <= batt_meter_cust_data.temperature_t1_5)')
  end=t.index('\t} else if (temperature <= batt_meter_cust_data.temperature_t2)',start)
  t=t[:start]+'\n#ifndef '+CFG+'\n'+t[start:end]+'\n#endif\n'+t[end:]
  # At 0..25 C select 0 C, not the absent 10 C table/Qmax/axis.
  start=t.index('\t} else if (temperature <= batt_meter_cust_data.temperature_t2)')
  end=t.index('\t} else {',start)
  part=t[start:end]
  part=part.replace('batt_meter_cust_data.temperature_t1_5','P00A_LOW_T2')
  part=part.replace('batt_meter_cust_data.q_max_pos_10_h_current','P00A_LOW_QMAX_HIGH')
  part=part.replace('batt_meter_cust_data.q_max_pos_10','P00A_LOW_QMAX')
  return t[:start]+part+t[end:]
 s=editfn(s,name,four)
anchor='signed int fgauge_get_Q_max(signed short temperature)'
s=s.replace(anchor,'''#ifdef CONFIG_ASUS_P00A_MAIN_BATTERY_SOC
#define P00A_LOW_T2 batt_meter_cust_data.temperature_t1
#define P00A_LOW_QMAX batt_meter_cust_data.q_max_pos_0
#define P00A_LOW_QMAX_HIGH batt_meter_cust_data.q_max_pos_0_h_current
#else
#define P00A_LOW_T2 batt_meter_cust_data.temperature_t1_5
#define P00A_LOW_QMAX batt_meter_cust_data.q_max_pos_10
#define P00A_LOW_QMAX_HIGH batt_meter_cust_data.q_max_pos_10_h_current
#endif

'''+anchor,1)
# Missing ten-degree parser would alias t1 (temperature_t1_5 starts as zero).
for prop in ['battery_profile_t1_5','r_profile_t1_5']:
 start=s.index('\t__batt_meter_parse_node(np, "'+prop+'_num"')
 end=s.index('\n\t__batt_meter_parse_node',start+2)
 s=s[:start]+'#ifndef '+CFG+'\n'+s[start:end]+'\n#endif\n'+s[end:]
# Multi-battery parser itself is #ifdef; baseline call was not.
s=s.replace('''\t} else
\t\t__batt_meter_parse_multi_battery_data(np, g_fg_battery_id);''','''\t}
#ifdef CONFIG_MTK_MULTI_BAT_PROFILE_SUPPORT
\telse
\t\t__batt_meter_parse_multi_battery_data(np, g_fg_battery_id);
#endif''',1)
# Mark model available only after successful parsing while locked against sampling.
s=override(s,'batt_meter_init_cust_data','''\tint ret = 0;

\tmutex_lock(&FGADC_mutex);
\tif (!init_done) {
\t\tret = __batt_meter_init_cust_data_from_dt();
\t\tif (!ret) {
\t\t\tinit_done = 1;
\t\t\tp00a_model_ready = true;
\t\t}
\t}
\tmutex_unlock(&FGADC_mutex);
\treturn ret;''')
# A raw 104-entry profile has repeated tail voltages/DODs. Exact endpoints and
# zero-length segments must never divide by zero. Preserve all pairs.
for name,field,arg in [('fgauge_read_capacity_by_v','voltage','voltage'),('fgauge_read_d_by_v','voltage','volt_bat'),('fgauge_read_r_bat_by_v','voltage','voltage'),('fgauge_read_v_by_d','percentage','d_val'),('fgauge_read_v_by_capacity','percentage','bat_capacity')]:
 def endpoints(t):
  if field=='voltage':
   t=t.replace(f'if ({arg} > (profile_p + 0)->voltage)',f'if ({arg} >= (profile_p + 0)->voltage)')
   # At the repeated minimum voltage, preserve ASUS's FIRST matching
   # segment (its DOD/R may differ from the final duplicate tail pair).
  else:
   t=t.replace(f'if ({arg} < (profile_p + 0)->percentage)\n\t\treturn 3700;',f'if ({arg} <= (profile_p + 0)->percentage)\n\t\treturn profile_p[0].voltage;')
   # Choose the FIRST matching DOD segment (as existing algorithm), not last
   # 100%-DOD tail; loop below does this for exactly 100.
   t=t.replace(f'if ({arg} > (profile_p + saddles - 1)->percentage)\n\t\treturn 3700;',f'if ({arg} > (profile_p + saddles - 1)->percentage)\n\t\treturn profile_p[saddles - 1].voltage;')
  t=t.replace('for (i = 0; i < saddles - 1; i++) {','for (i = 0; i < saddles - 1; i++) {\n\t\tif (profile_p[i].'+field+' == profile_p[i + 1].'+field+')\n\t\t\tcontinue;',1)
  return t
 s=editfn(s,name,endpoints)
# Disallow legacy resampling/aging paths for the board. This also avoids the
# five-axis resampler indexing a four-element profile pointer array.
for name in ['fgauge_construct_battery_profile_init','fgauge_construct_table_by_temp','fg_qmax_update_for_aging','table_init']:
 s=override(s,name,'\t/* The checked board transaction owns model construction. */\n\treturn;')
# OAM D2 is independent of D1/D3/D5; the board DT explicitly selects D2.
# It is staged in a testable include after the existing lookup/interpolation helpers.
anchor='void oam_init(void)'
s=s.replace(anchor,'#ifdef '+CFG+'\n#include "asus_p00a_soc.inc"\n#endif\n\n'+anchor,1)
s=s.replace('unsigned int charging_enable;','unsigned int charging_enable = false;',1)
for name in ['oam_init','oam_run']:
 s=override(s,name,'\tasus_p00a_soc_update();')
for name in ['battery_meter_get_battery_percentage','battery_meter_get_battery_soc']:
 s=override(s,name,'\tint soc, ret = asus_p00a_soc_capacity(&soc);\n\n\treturn ret ? ret : soc;')
s=override(s,'battery_meter_initial','\treturn asus_p00a_soc_update();')
s=override(s,'battery_meter_reset','\t/* UI tracking cannot overwrite a measured model state. */\n\treturn -EOPNOTSUPP;')
for name in ['reset_parameter_car','reset_parameter_dod_change','reset_parameter_dod_full']:
 s=override(s,name,'\t/* Unsupported UI-SOC mutation; state belongs to the board transaction. */\n\treturn;')
# Lifetime fields do not exist when the unsupported configuration is disabled.
s=editfn(s,'battery_meter_get_data',lambda t:t.replace('\n\tif (!data)','\n#if defined(CONFIG_MTK_BATTERY_LIFETIME_DATA_SUPPORT)\n\tif (!data)').replace('\n\treturn 0;','\n\treturn 0;\n#else\n\treturn -EOPNOTSUPP;\n#endif'))
s=override(s,'battery_meter_suspend','\tasus_p00a_soc_suspend(true);\n\treturn 0;')
s=override(s,'battery_meter_resume','\tasus_p00a_soc_suspend(false);\n\tbat_spm_timeout = true;\n\twake_up_bat();\n\treturn 0;')
write(p,s)
p='drivers/misc/mediatek/include/mt-plat/battery_meter_table.h';s=read(p).replace('#define PROFILE_TABLE_SIZE    100','#ifdef '+CFG+'\n#define PROFILE_TABLE_SIZE    104\n#else\n#define PROFILE_TABLE_SIZE    100\n#endif');write(p,s)
p='arch/arm64/configs/asus_p00a_defconfig';s=read(p)
for c in ['CONFIG_MTK_MULTI_BAT_PROFILE_SUPPORT','CONFIG_MTK_BATTERY_LIFETIME_DATA_SUPPORT']:
 s=s.replace(c+'=y','# '+c+' is not set')
s+='\n'+CFG+'=y\n';write(p,s)
p='drivers/power/supply/mediatek/battery/Kconfig';s=read(p)+'''
config ASUS_P00A_MAIN_BATTERY_SOC
	bool "ASUS P00A checked main-battery OAM SOC"
	depends on ASUS_P00A_BATTERY_DIAGNOSTIC && OF
	depends on !MTK_MULTI_BAT_PROFILE_SUPPORT
	depends on !MTK_BATTERY_LIFETIME_DATA_SUPPORT
	help
	  Use the ASUS four-temperature, 104-pair pad battery model with
	  checked ADC samples, bounded freshness and error-aware SOC.
	  Charging remains inhibited; this does not opt in to charging.
''';write(p,s)
# Add a checked batch reader and capacity dispatch to previous measurement code.
p='include/linux/power/asus_p00a_battery.h';s=read(p).replace('#endif','''#ifdef CONFIG_ASUS_P00A_MAIN_BATTERY_SOC
struct asus_p00a_battery_sample {
	int voltage_mv;
	int temperature_decic;
	int status;
	int capacity;
};
int asus_p00a_pmic_enable_baton(void);
int asus_p00a_battery_read_sample(struct asus_p00a_battery_sample *sample);
int asus_p00a_soc_update(void);
int asus_p00a_soc_capacity(int *capacity);
int asus_p00a_soc_read(struct asus_p00a_battery_sample *sample);
void asus_p00a_soc_invalidate(int error);
void asus_p00a_soc_suspend(bool suspended);
#endif
#endif''');write(p,s)
p='drivers/misc/mediatek/power/mt8163/asus_p00a/battery_diag.c';s=read(p).replace('independent of the unvalidated SW estimator.','with checked SOC provided by the board OAM transaction.')
s=s.replace('case POWER_SUPPLY_PROP_CAPACITY:\n','''case POWER_SUPPLY_PROP_CAPACITY:
#ifdef CONFIG_ASUS_P00A_MAIN_BATTERY_SOC
		return asus_p00a_soc_capacity(&val->intval);
#endif
''',1)
# Reader intentionally calls the measurement primitives, not the public capacity path.
s+='''
#ifdef CONFIG_ASUS_P00A_MAIN_BATTERY_SOC
int asus_p00a_battery_read_sample(struct asus_p00a_battery_sample *sample)
{
	struct asus_p00a_battery_sample next = { 0 };
	int present, mv, ret;

	ret = asus_p00a_pmic_present(&present);
	if (ret || !present)
		return ret ? ret : -ENODEV;
	ret = asus_p00a_pmic_adc(6, 5, &next.voltage_mv);
	if (ret)
		return ret;
	if (next.voltage_mv < 2000 || next.voltage_mv > 5000)
		return -ERANGE;
	ret = asus_p00a_pmic_adc(5, 5, &mv);
	if (ret)
		return ret;
	ret = p00a_battery_temperature(mv, &next.temperature_decic);
	if (ret)
		return ret;
	ret = asus_p00a_charger_status(&next.status);
	if (ret)
		return ret;
	/* Charging is not supported by this product. Do not model an unexpected
	 * enabled charger as a valid inhibited-charging observation.
	 */
	if (next.status != POWER_SUPPLY_STATUS_DISCHARGING &&
	    next.status != POWER_SUPPLY_STATUS_NOT_CHARGING)
		return -EPERM;
	ret = asus_p00a_pmic_present(&present);
	if (ret || !present)
		return ret ? ret : -ENODEV;
	*sample = next;
	return 0;
}
#endif
''';write(p,s)
p='drivers/misc/mediatek/power/mt8163/asus_p00a/pmic_battery.inc';s=read(p)+'''
#ifdef CONFIG_ASUS_P00A_MAIN_BATTERY_SOC
int asus_p00a_pmic_enable_baton(void)
{
	int ret, present;

	if (!READ_ONCE(pmicAuxadc_irq_lock) || !READ_ONCE(pwrap_regmap))
		return -ENODATA;
	__pm_stay_awake(pmicAuxadc_irq_lock);
	mutex_lock(&pmic_adc_mutex);
	ret = p00a_pmic_result(pmic_config_interface(CHR_CON7, 1,
			PMIC_BATON_TDET_EN_MASK, PMIC_BATON_TDET_EN_SHIFT));
	if (!ret)
		ret = p00a_pmic_result(pmic_config_interface(CHR_CON7, 1,
			PMIC_RG_BATON_EN_MASK, PMIC_RG_BATON_EN_SHIFT));
	/* The existing battery check enables the same detector. Read back its
	 * enables through the checked presence helper; never trust reset bits.
	 */
	if (!ret) {
		usleep_range(1000, 2000);
		ret = asus_p00a_pmic_present(&present);
	}
	mutex_unlock(&pmic_adc_mutex);
	__pm_relax(pmicAuxadc_irq_lock);
	return ret;
}
#endif
''';write(p,s)
p='drivers/power/supply/mediatek/battery/battery_common.c';s=read(p)
# Preserve charger detection/USB reporting and actual thermal shutdown. Avoid
# old UI tracking, aging resets, simulated currents and charger reprogramming.
s=override(s,'BAT_thread','''\tstruct asus_p00a_battery_sample sample;
\tunsigned int charging_enable = false;
\tint ret;

\tmt_battery_charger_detect_check();
\tret = asus_p00a_soc_update();
\tif (!ret)
\t\tret = asus_p00a_soc_read(&sample);
\tif (!ret) {
\t\tBMT_status.bat_vol = sample.voltage_mv;
\t\tBMT_status.temperature = sample.temperature_decic / 10;
\t\tBMT_status.bat_exist = true;
\t\tBMT_status.SOC = sample.capacity;
\t\tBMT_status.UI_SOC = sample.capacity;
\t\tg_battery_soc_ready = true;
\t\tmt_battery_thermal_check();
\t} else {
\t\t/* These internal fields must not look like fresh charge inputs. */
\t\tBMT_status.bat_vol = 0;
\t\tBMT_status.temperature = -127;
\t\tBMT_status.SOC = -1;
\t\tBMT_status.UI_SOC = -1;
\t\tg_battery_soc_ready = false;
\t\tpr_warn_ratelimited("P00A battery sample unavailable: %d\\n", ret);
\t}
\t/* The independent BQ guard also runs every five seconds. */
\tbattery_charging_control(CHARGING_CMD_ENABLE, &charging_enable);
\tusb_update(&usb_main);
\tac_update(&ac_main);
\tpower_supply_changed(battery_main.psy);''')
# Auxiliary HV thread must not turn failed detector reads into battery absence.
s=override(s,'check_battery_exist','''\tunsigned int charging_enable = false;
\tint present, ret;

\tret = asus_p00a_pmic_enable_baton();
\tif (!ret)
\t\tret = asus_p00a_pmic_present(&present);
\tif (ret || !present) {
\t\tasus_p00a_soc_invalidate(ret ? ret : -ENODEV);
\t\tbattery_charging_control(CHARGING_CMD_ENABLE, &charging_enable);
\t\tif (!ret)
\t\t\tbattery_charging_control(CHARGING_CMD_SET_POWER_OFF, NULL);
\t}''')
# IRQ callback must not sleep for the two-sample initialization. Normal battery
# worker performs it, including after insertion/wakeup.
s=s.replace('''\t\tif (g_battery_soc_ready == false) {''','''#ifndef CONFIG_ASUS_P00A_MAIN_BATTERY_SOC
\t\tif (g_battery_soc_ready == false) {''',1)
pos=s.index('\n\t\tif (BMT_status.bat_vol > 0)',s.index('#ifndef CONFIG_ASUS_P00A_MAIN_BATTERY_SOC\n\t\tif (g_battery_soc_ready'))
s=s[:pos]+'\n#endif\n'+s[pos:]
write(p,s)
print('Staged kernel integration; production OAM include is maintained separately.')
# Reject failed live measurements immediately instead of leaving model validity
# true until the next worker tick. Unsupported optional properties do not count.
p='drivers/misc/mediatek/power/mt8163/asus_p00a/battery_diag.c';s=(OUT/p).read_text()
s=s.replace('int asus_p00a_battery_get_property(enum power_supply_property property,','static int p00a_measurement_get_property(enum power_supply_property property,',1)
s+='''
int asus_p00a_battery_get_property(enum power_supply_property property,
				 union power_supply_propval *val)
{
	int ret = p00a_measurement_get_property(property, val);

#ifdef CONFIG_ASUS_P00A_MAIN_BATTERY_SOC
	switch (property) {
	case POWER_SUPPLY_PROP_PRESENT:
		if (!ret && !val->intval)
			asus_p00a_soc_invalidate(-ENODEV);
		/* fall through */
	case POWER_SUPPLY_PROP_STATUS:
	case POWER_SUPPLY_PROP_VOLTAGE_NOW:
	case POWER_SUPPLY_PROP_batt_vol:
	case POWER_SUPPLY_PROP_TEMP:
	case POWER_SUPPLY_PROP_batt_temp:
		if (ret)
			asus_p00a_soc_invalidate(ret);
		break;
	default:
		break;
	}
#endif
	return ret;
}
''';write(p,s)
# The battery thermal zone must propagate sensor errno, not treat errno as a
# temperature or synthesize its old 25 C boot value. Board thermistor untouched.
p='drivers/misc/mediatek/thermal/mt8163/mtk_ts_battery.c';s=read(p)
s=s.replace('#include "mt-plat/battery_meter.h"','#include "mt-plat/battery_meter.h"\n#include <linux/power/asus_p00a_battery.h>')
old='''\t*t = mtktsbattery_get_hw_temp();
\tif((int)*t >= polling_trip_temp_high)
\t\t*t = battery_meter_get_battery_temperature() * 1000;'''
new='''#ifdef CONFIG_ASUS_P00A_MAIN_BATTERY_SOC
\tunion power_supply_propval value;
\tint ret = asus_p00a_battery_get_property(POWER_SUPPLY_PROP_TEMP, &value);

\tif (ret)
\t\treturn ret;
\t*t = value.intval * 100;
#else
'''+old+'''\n#endif'''
assert old in s;s=s.replace(old,new,1)
# These are used only by the legacy thermal branch.
s=s.replace('static int mtktsbattery_get_hw_temp(void)','static int __maybe_unused mtktsbattery_get_hw_temp(void)')
write(p,s)
p='drivers/power/supply/mediatek/battery/battery_common.c';s=(OUT/p).read_text()
a,b,c=fnspan(s,'bat_thread_kthread');t=s[a:c]
start=t.index('\tif (is_usb_rdy() == false) {');end=t.index('\n\t/* Run on a process content */',start)
t=t[:start]+'#ifndef '+CFG+'\n'+t[start:end]+'\n#endif\n'+t[end:]
s=s[:a]+t+s[c:]
# GPIO/USB detection may wait for USB initialization; battery modeling must not.
a,b,c=fnspan(s,'BAT_thread');t=s[a:c]
t=t.replace('\tmt_battery_charger_detect_check();','\tif (is_usb_rdy())\n\t\tmt_battery_charger_detect_check();',1)
s=s[:a]+t+s[c:];write(p,s)
# Keep shared legacy helpers buildable when their board call sites are compiled
# out. Kernel's Werror build enables unused-function/variable diagnostics.
p='drivers/power/supply/mediatek/battery/battery_common.c';s=(OUT/p).read_text()
for name in ['mt_battery_CheckBatteryStatus','mt_battery_update_status','mt_kpoc_power_off_check','mt_otg_check']:
 s=re.sub(r'(static\s+)([^;{}\n]*\b'+name+r'\s*\()',r'\1__maybe_unused \2',s,count=1)
for name in ['bat_7days_flag','bat_demo_flag']:
 s=re.sub(r'(static\s+bool\s+)('+name+r'\b)',r'\1__maybe_unused \2',s,count=1)
write(p,s)
p='drivers/power/supply/mediatek/battery/battery_meter.c';s=(OUT/p).read_text().replace('static bool g_skip_reset_sleep_time;','static bool __maybe_unused g_skip_reset_sleep_time;');write(p,s)
p='drivers/power/supply/mediatek/battery/battery_common.c';s=(OUT/p).read_text()
s=s.replace('''\t/* The independent BQ guard also runs every five seconds. */
\tbattery_charging_control(CHARGING_CMD_ENABLE, &charging_enable);''','''\t/* Successful transactions already checked charging inhibition. On every
\t * failure, request it again; the independent BQ guard also runs at 5s.
\t */
\tif (ret)
\t\tbattery_charging_control(CHARGING_CMD_ENABLE, &charging_enable);''',1)
write(p,s)
p='drivers/power/supply/mediatek/battery/Kconfig';s=(OUT/p).read_text().replace('''\t  current and charge counters return ENODATA pending software gauge
\t  reconciliation. This does not grant permission to charge.''','''\t  current and charge counters return ENODATA unless the checked SOC
\t  option below supplies initialized capacity. Current/counters remain
\t  unsupported. This does not grant permission to charge.''');write(p,s)
