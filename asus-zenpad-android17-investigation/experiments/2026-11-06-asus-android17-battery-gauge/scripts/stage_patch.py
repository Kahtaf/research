#!/usr/bin/env python3
"""Build the text patch from pinned source and the reviewed staged additions."""
from pathlib import Path
import difflib, hashlib, json
root=Path(__file__).resolve().parents[1]
base=root/'evidence/base'
stage=root/'staged'
def change(path, old, new):
    p=stage/path
    s=(base/path).read_text()
    assert s.count(old)==1, (path,s.count(old))
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(s.replace(old,new))
change('drivers/misc/mediatek/power/mt8163/pmic_mt6323.c',
       'int PMIC_IMM_GetOneChannelValue(unsigned int dwChannel, int deCount,',
       '#ifdef CONFIG_ASUS_P00A_BATTERY_DIAGNOSTIC\n#include "asus_p00a/pmic_battery.inc"\n#endif\n\nint PMIC_IMM_GetOneChannelValue(unsigned int dwChannel, int deCount,')
# Route legacy users of these same channels through the serialized checked reader.
p=stage/'drivers/misc/mediatek/power/mt8163/pmic_mt6323.c'
s=p.read_text(); old='\t/* do not support BATON2 and THR SENSE2 for sw workaround */'
assert s.count(old)==1
s=s.replace(old, '''#ifdef CONFIG_ASUS_P00A_BATTERY_DIAGNOSTIC
	if (dwChannel >= 4 && dwChannel <= 7) {
		int mv, ret;

		ret = asus_p00a_pmic_adc(dwChannel, deCount, &mv);
		return ret ? ret : mv;
	}
#endif

'''+old);p.write_text(s)
change('drivers/misc/mediatek/power/mt8163/asus_p00a/Makefile',
       'obj-y += bq25896.o', 'obj-y += bq25896.o\nobj-$(CONFIG_ASUS_P00A_BATTERY_DIAGNOSTIC) += battery_diag.o')
change('drivers/misc/mediatek/power/mt8163/asus_p00a/bq25896.c',
       '#include "control.h"', '#include "control.h"\n#ifdef CONFIG_ASUS_P00A_BATTERY_DIAGNOSTIC\n#include "battery_status.inc"\n#endif')
change('drivers/power/supply/mediatek/battery/battery_common.c',
       'static int battery_get_property(struct power_supply *psy,',
       '#ifdef CONFIG_ASUS_P00A_BATTERY_DIAGNOSTIC\n#include <linux/power/asus_p00a_battery.h>\n#endif\n\nstatic int battery_get_property(struct power_supply *psy,')
p=stage/'drivers/power/supply/mediatek/battery/battery_common.c';s=p.read_text()
old='\t\tcontainer_of(psy->desc, struct battery_data, psd);\n\n\tswitch (psp) {'
assert s.count(old)==1
s=s.replace(old, '''		container_of(psy->desc, struct battery_data, psd);

#ifdef CONFIG_ASUS_P00A_BATTERY_DIAGNOSTIC
	return asus_p00a_battery_get_property(psp, val);
#endif

	switch (psp) {''')
p.write_text(s)
change('drivers/power/supply/mediatek/battery/Kconfig',
       'config ASUS_P00A_BQ25896', '''config ASUS_P00A_BATTERY_DIAGNOSTIC
	bool "ASUS P00A measured battery diagnostics"
	depends on ASUS_P00A_BQ25896 && MTK_PMIC
	default n
	help
	  Expose checked MT6323 battery voltage, temperature and presence plus
	  BQ25896 charge state on the existing battery power supply. Capacity,
	  current and charge counters return ENODATA pending software gauge
	  reconciliation. This does not grant permission to charge.

config ASUS_P00A_BQ25896''')
change('arch/arm64/configs/asus_p00a_defconfig',
       'CONFIG_ASUS_P00A_BQ25896=y',
       'CONFIG_ASUS_P00A_BQ25896=y\nCONFIG_ASUS_P00A_BATTERY_DIAGNOSTIC=y')
change('drivers/misc/mediatek/include/mt-plat/mt8163/include/mach/mtk_battery_meter.h',
       '#define VBATTEMP_CHANNEL_NUMBER  3', '''#define VBATTEMP_CHANNEL_NUMBER  3

#ifdef CONFIG_ASUS_P00A_BATTERY_DIAGNOSTIC
/* ASUS MT6323 routing; channel 0 is unsupported on this PMIC. */
#undef VBAT_CHANNEL_NUMBER
#undef ISENSE_CHANNEL_NUMBER
#undef VCHARGER_CHANNEL_NUMBER
#undef VBATTEMP_CHANNEL_NUMBER
#define VBAT_CHANNEL_NUMBER 6
#define ISENSE_CHANNEL_NUMBER 7
#define VCHARGER_CHANNEL_NUMBER 4
#define VBATTEMP_CHANNEL_NUMBER 5
#ifndef SWCHR_POWER_PATH
#define SWCHR_POWER_PATH
#endif
#ifndef BAT_VOL_USE_ISENSE
#define BAT_VOL_USE_ISENSE
#endif
#ifndef EXTERNAL_SWCHR_SUPPORT
#define EXTERNAL_SWCHR_SUPPORT
#endif
#endif''')
# The legacy algorithm keeps running internally: correct its routing without
# advertising its unvalidated estimates through the Health path.
change('arch/arm64/boot/dts/mediatek/asus8163_tb_380_m_bat_setting.dtsi',
       '&bat_meter {', '''&bat_meter {
	/* ASUS main pad battery, not the optional UG31xx cover. */
	vbat_channel_number = <6>;
	isense_channel_number = <7>;
	vcharger_channel_number = <4>;
	vbattemp_channel_number = <5>;
	swchr_power_path = <1>;
	rbat_pull_down_r = <30000>;''')
patch=[];manifest={}
for p in sorted(stage.rglob('*')):
    if not p.is_file():continue
    rel=p.relative_to(stage).as_posix(); before=base/rel
    old=before.read_text().splitlines(True) if before.exists() else []
    new=p.read_text().splitlines(True)
    if old==new:continue
    patch.append('diff --git a/'+rel+' b/'+rel+'\n')
    if not before.exists():patch.append('new file mode 100644\n')
    patch.extend(difflib.unified_diff(old,new,fromfile='a/'+rel if before.exists() else '/dev/null',tofile='b/'+rel))
    manifest[rel]={'base':hashlib.sha256(before.read_bytes()).hexdigest() if before.exists() else None,'staged':hashlib.sha256(p.read_bytes()).hexdigest()}
(root/'patches/0001-asus-p00a-measured-battery.patch').write_text(''.join(patch))
(root/'evidence/patch-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Staged',len(manifest),'source files.')
