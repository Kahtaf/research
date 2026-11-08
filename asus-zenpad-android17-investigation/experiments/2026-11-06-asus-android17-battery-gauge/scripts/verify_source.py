#!/usr/bin/env python3
"""Verify provenance, source wiring and patch replay; never reads private data."""
from pathlib import Path
import hashlib, json, re, shutil, subprocess
r=Path(__file__).resolve().parents[1]; b=r/'evidence/base'; s=r/'staged'
stock=r.parent/'2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18'
m=json.loads((r/'evidence/patch-manifest.json').read_text())
checks=[]
def check(name,ok):
    checks.append({'check':name,'pass':bool(ok)})
    assert ok,name
read=lambda p:p.read_text(errors='strict')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
remote=json.loads((r/'evidence/remote-source.json').read_text())
for p,h in remote['sha256'].items():check('pinned source hash '+p,sha(b/p)==h)
for p,h in m.items():
    check('staged hash '+p,sha(s/p)==h['staged'])
    if h['base']:check('patch base hash '+p,sha(b/p)==h['base'])
# Independently derive MT6323 output registers from the pinned upstream accessors.
sw=read(b/'drivers/misc/mediatek/include/mt-plat/mt8163/include/mach/upmu_sw.h')
expected=['vcdt','baton1','isense','batsns']; regs=[]
for name in expected:
    func=sw.split('upmu_get_rg_adc_out_'+name+'(void)',1)[1].split('\n}',1)[0]
    regs.append(re.search(r'\((AUXADC_ADC\d+)\)',func)[1])
inc=read(s/'drivers/misc/mediatek/power/mt8163/asus_p00a/pmic_battery.inc')
arr=inc.split('output_reg[] = {',1)[1].split('}',1)[0]
check('ADC4..7 mappings match real pinned PMIC accessors',re.findall('AUXADC_ADC[0-9]+',arr)==regs)
old=read(stock/'drivers/misc/mediatek/include/mt-plat/mt8163/include/mach/mt_battery_meter_table.h')
orig=re.search(r'Batt_Temperature_Table\[2\]\[17\] = \{(.*?)\n\};',old,re.S)[1]
pairs=[tuple(map(int,x)) for x in re.findall(r'\{\s*(-?\d+)\s*,\s*(\d+)\}',orig)]
new=read(s/'drivers/misc/mediatek/power/mt8163/asus_p00a/battery_diag.c')
new_r=list(map(int,re.findall(r'\d+',new.split('p00a_ntc_ohms[] = {')[1].split('}')[0])))
check('all 17 ASUS battery NTC pairs match GPL source',pairs==list(zip(range(-20,61,5),new_r)))
check('battery resistor network matches ASUS source',all(re.search(r'#define\s+'+key+r'\s+'+str(value)+r'\b',old) for key,value in [('RBAT_PULL_UP_R',16900),('RBAT_PULL_DOWN_R',30000),('RBAT_PULL_UP_VOLT',1800)]))
common=read(s/'drivers/power/supply/mediatek/battery/battery_common.c')
props=common.split('static enum power_supply_property battery_props[] = {',1)[1].split('};',1)[0]
check('standard voltage property appears once',props.count('POWER_SUPPLY_PROP_VOLTAGE_NOW')==1)
check('diagnostic dispatch precedes legacy caches',common.index('return asus_p00a_battery_get_property(psp, val);')<common.index('val->intval = data->BAT_STATUS;'))
check('charger fault latch not consumed by status reader','REG_FAULT' not in read(s/'drivers/misc/mediatek/power/mt8163/asus_p00a/battery_status.inc'))
check('charging policy source unchanged', 'drivers/misc/mediatek/power/mt8163/asus_p00a/control.h' not in m)
dts=read(b/'arch/arm64/boot/dts/mediatek/asus-p00a.dts')
# Ignore commentary mentioning the opt-in: check an actual property declaration.
check('charging opt-in absent',not re.search(r'^\s*asus,allow-battery-charging\s*;',dts,re.M))
check('main board charging DT unchanged','arch/arm64/boot/dts/mediatek/asus-p00a.dts' not in m)
status=read(s/'drivers/misc/mediatek/power/mt8163/asus_p00a/battery_status.inc')
check('read-only BQ status path',not any(x in status for x in ['regmap_write','regmap_update_bits','p00a_apply','p00a_command']))
check('new PMIC path never calls unbounded old ADC preparation','PMIC_IMM_PollingAuxadcChannel();' not in inc)
check('ADC polls bounded',inc.count('< ADC_COUNT_TIMEOUT')==2)
# Replay in an isolated, selective source fixture, not a kernel build tree.
replay=r/'evidence/replay'
if replay.exists():shutil.rmtree(replay)
replay.mkdir()
for p,h in m.items():
    if h['base']:
        out=replay/p;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(b/p,out)
subprocess.run(['git','init','-q',str(replay)],check=True)
patch=r/'patches/0001-asus-p00a-measured-battery.patch'
checkcmd=['git','-C',str(replay),'apply','--check',str(patch)]
subprocess.run(checkcmd,check=True)
subprocess.run(['git','-C',str(replay),'apply',str(patch)],check=True)
for p,h in m.items():check('patch replays exactly '+p,sha(replay/p)==h['staged'])
(r/'evidence/source-checks.json').write_text(json.dumps({'checks':checks,'passed':len(checks),'patch_sha256':sha(patch),'scope':'selected files only; no full kernel compilation','patch_check_command':checkcmd},indent=2)+'\n')
print('PASS:',len(checks),'source/provenance/guard/replay checks')
