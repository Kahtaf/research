#!/usr/bin/env python3
from pathlib import Path
import subprocess,shutil,json,hashlib,re
R=Path(__file__).resolve().parents[1];B=R/'source/kernel-after-soc';S=R/'staged';W=R/'evidence/replay'
checks=[]
def check(v,name):
 assert v,name
 checks.append(name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((R/'evidence/patch-manifest.json').read_text())
frozen=json.loads((R/'evidence/frozen-source-sha256.json').read_text())
for p,h in frozen.items():check(sha(R/'source'/p)==h,'frozen '+p)
if W.exists():shutil.rmtree(W)
shutil.copytree(R/'source/kernel-base',W)
subprocess.run(['git','init','-q',str(W)],check=True)
for path in [R/'source'/n for n in m['prerequisites']]+[R/'patches'/m['patch']]:
 subprocess.run(['git','-C',str(W),'apply','--check','--whitespace=error-all',str(path)],check=True)
 subprocess.run(['git','-C',str(W),'apply','--whitespace=error-all',str(path)],check=True)
 check(True,'sequential patch replay '+path.name)
for p,h in m['files'].items():check(sha(W/p)==h['after']==sha(S/p),'byte-identical replay '+p)
for p,h in m['unchanged_guards'].items():check(sha(W/p)==h,'unchanged '+p)
check(sha(R/'patches'/m['patch'])==m['sha256'],'patch hash')
for n,h in m['prerequisites'].items():check(sha(R/'source'/n)==h,'prerequisite hash '+n)
b=S/'drivers/misc/mediatek/power/mt8163/asus_p00a'
control=(b/'control.h').read_text();snapshot=(b/'charge_snapshot.inc').read_text();driver=(b/'bq25896.c').read_text();soc=(S/'drivers/power/supply/mediatek/battery/asus_p00a_soc.inc').read_text()
check('BMT_status' not in control,'no cached BMT status charger input')
check('asus_p00a_soc_read(' not in control+snapshot+driver,'no charger-to-SOC lock edge')
check('asus_p00a_charge_publish(NULL' in soc,'model errors publish synchronous invalidation')
check('asus_p00a_charge_publish(&p00a_oam.sample' in soc,'successful OAM transaction publishes generation')
check('get_monotonic_boottime' in driver and 'get_monotonic_boottime' in soc,'shared boottime domain')
reads=re.findall(r'regmap_read\([^;]*REG_FAULT[^;]*;',control)
check(len(reads)==2,'only two hardware fault reads')
start=control.index('static int p00a_fault_sample');end=control.index('static int p00a_source',start)
check(all(x in control[start:end] for x in reads),'only guard owns fault latch')
check('regmap_read' not in snapshot[:snapshot.index('static ssize_t charge_guard_show')],'snapshot publication has no recursive telemetry')
check('if (i == REG_FAULT)' in snapshot,'read-only telemetry skips fault latch')
check('if (value == REG_FAULT)' in control,'legacy dump skips fault latch')
check('p->fault_latched |= first & 0xf8;' in control,'first consumed fault retained before second read')
check('p00a_verify(p, REG_TIMER, 0xb8, 0x88)' in control,'safety timer and termination verified, watchdog disabled')
check('p00a_write_checked(p, REG_CONTROL, CHG_ENABLE, CHG_ENABLE)' in control,'enable requires actual readback')
check('p->disable_error = ret ? ret : read_ret;' in control,'failed disable writes not converted to success')
check('DEVICE_ATTR_RO(charge_guard)' in snapshot and 'DEVICE_ATTR_RW' not in snapshot,'no arbitrary register writer')
check('hw_charger_type_detection()' not in control,'unchecked PMIC classifier not trusted')
check('p00a_bc12_read' in (b/'bc12.inc').read_text(),'checked BC1.2 sequence staged')
check('pm_stay_awake' in control and 'p00a_quiesce(p)' in driver,'runtime supervision and conservative suspend')
check('4208000' in snapshot and '51200' in snapshot,'bounded runtime request below original ceilings')
check('P00A_CV_MAX_UV 4352000U' in (b/'policy.h').read_text(),'original voltage ceiling retained')
check('P00A_ICHG_MAX_MA 1920U' in (b/'policy.h').read_text(),'original current ceiling retained')
check('asus,allow-battery-charging' not in (B/'arch/arm64/boot/dts/mediatek/asus-p00a.dts').read_text(),'DT permission absent')
check(not any('boot/dts' in p for p in m['files']),'patch does not edit DT')
config=(B/'arch/arm64/configs/asus_p00a_defconfig').read_text()
for n in ['ASUS_P00A_BQ25896','ASUS_P00A_BATTERY_DIAGNOSTIC','ASUS_P00A_MAIN_BATTERY_SOC','MTK_SMART_BATTERY','MTK_PMIC']:
 check('CONFIG_'+n+'=y' in config,'required frozen defconfig '+n)
for n in ['MTK_MULTI_BAT_PROFILE_SUPPORT','MTK_BATTERY_LIFETIME_DATA_SUPPORT']:
 check('CONFIG_'+n+'=y' not in config,'unsupported model disabled '+n)
check('asus_p00a_charge_source_changed();' in (S/'drivers/power/supply/mediatek/battery/battery_common.c').read_text(),'real threaded CHRDET caller invalidates caps/sample')
check('p00a_next_poll(p)' in driver,'monitor schedules sample deadline')
check('p00a_write_checked(p, REG_ADC, BIT(7), BIT(7))' in control,'BQ ADC busy transition must be observed')
# Match every reused production model function to the frozen after-SOC source.
def function(text,name):
 match=re.search(r'\b'+re.escape(name)+r'\([^;{}]*\)\s*\{',text);assert match,name
 start=text.rfind('\n',0,match.start())+1;i=text.index('{',match.start())+1;depth=1
 while depth:
  if text[i]=='{':depth+=1
  elif text[i]=='}':depth-=1
  i+=1
 return text[start:i]
meter=(B/'drivers/power/supply/mediatek/battery/battery_meter.c').read_text()
fixture=(R/'source/test-fixtures/model_functions.h').read_text()
for name in ['fgauge_get_saddles','fgauge_get_saddles_r_table','fgauge_get_profile','fgauge_get_profile_r_table','fgauge_get_Q_max','fgauge_get_Q_max_high_current','fgauge_construct_battery_profile','fgauge_construct_r_table_profile','fgauge_read_capacity_by_v','fgauge_read_d_by_v','fgauge_read_v_by_d','fgauge_read_v_by_capacity','fgauge_read_r_bat_by_v','__batt_meter_parse_table']:
 check(function(meter,name)==function(fixture,name),'production model fixture '+name)
# Check BC1.2 masks against the pinned PMIC field declarations.
hw=(B/'drivers/misc/mediatek/include/mt-plat/mt8163/include/mach/upmu_hw.h').read_text()
for name,shift in [('BB_CTRL',0),('RST',1),('VSRC_EN',2),('VREF_VTH',0),('CMP_EN',2),('IPD_EN',4),('IPU_EN',6),('BIAS_EN',8)]:
 match=re.search(r'#define PMIC_RG_BC11_'+name+r'_SHIFT\s+(\d+)',hw)
 check(match and int(match.group(1))==shift,'BC1.2 source field '+name)
# Ensure prior evidence/fixtures are tied to the tested, frozen files.
h=json.loads((R/'evidence/host-checks.json').read_text())
for p,expected in h['tested_source_sha256'].items():check(sha(R/p)==expected,'tested current production '+p)
for n,t in h['tests'].items():check(t['compile_returncode']==t['run_returncode']==0,'host suite '+n)
(R/'evidence/source-checks.json').write_text(json.dumps({'passed':len(checks),'checks':checks,'scope':'subset replay/config/provenance only; not ARM64 compilation'},indent=2)+'\n')
print('PASS:',len(checks),'source, configuration, provenance and sequential-replay checks')
