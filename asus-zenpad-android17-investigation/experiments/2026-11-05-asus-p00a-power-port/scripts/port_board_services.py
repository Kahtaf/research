#!/usr/bin/env python3
from pathlib import Path
import re,json
root=Path(__file__).resolve().parents[1];src=root/'sources/kernel';old=root.parent/'2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18'
# GPIO85 is documented in the actual ASUS charger code as touch power. Give its
# ownership to the actual touch consumer, avoiding the stock double-request.
p=src/'drivers/misc/mediatek/power/mt8163/asus_p00a/bq25896.c';s=p.read_text();s=s.replace('\t\t{ "i2c_power_gpio", 1 },\n','');p.write_text(s)
p=src/'drivers/input/touchscreen/goodix.c';s=p.read_text().replace('#include <linux/of.h>','#include <linux/of.h>\n#include <linux/of_gpio.h>\n#include <linux/gpio.h>')
needle='\terror = goodix_get_gpio_config(ts);';assert s.count(needle)==1
s=s.replace(needle,'''\tif (of_device_is_compatible(client->dev.of_node, "goodix,gt6108")) {
		int power_gpio = of_get_named_gpio(client->dev.of_node, "power-gpio", 0);

		if (power_gpio < 0)
			return power_gpio;
		error = devm_gpio_request_one(&client->dev, power_gpio,
			GPIOF_OUT_INIT_HIGH, "asus-gt6108-power");
		if (error)
			return error;
		msleep(20);
	}

'''+needle);p.write_text(s)
# Preserve the ASUS thermistor curve and channel-0 hardware constants.
p=src/'drivers/misc/mediatek/thermal/mt8163/inc/mtk_ts_board_karnak.h';s=p.read_text();head=s.index('struct BTS_TEMPERATURE;')
new='''/* SPDX-License-Identifier: GPL-2.0-only */
/* ASUS GPL mtk_ts_bts.c: AUXADC0, 390k pull-up, 1.8V, NTC table 6. */
#define AUX_CHANNEL_NUM 1
struct mtkts_bts_channel_param;
static struct mtkts_bts_channel_param bts_channel_param[AUX_CHANNEL_NUM] = {
	{ 390000, 4251000, 1800, 6, 0, 0, "mtkts_bts0" },
};

'''+s[head:]
target=p.with_name('mtk_ts_board_asus_p00a.h');target.write_text(new)
p=src/'drivers/misc/mediatek/thermal/mt8163/mtk_ts_bts.c';s=p.read_text();s=s.replace('#elif defined(CONFIG_THERMAL_KARNAK)','#elif defined(CONFIG_THERMAL_ASUS_P00A)\n#include "inc/mtk_ts_board_asus_p00a.h"\n#elif defined(CONFIG_THERMAL_KARNAK)',1);p.write_text(s)
p=src/'drivers/misc/mediatek/thermal/Kconfig';s=p.read_text();s+='\nconfig THERMAL_ASUS_P00A\n\tbool "ASUS P00A board thermistor"\n\tdefault n\n';p.write_text(s)
p=src/'arch/arm64/boot/dts/mediatek/asus-p00a.dts';s=p.read_text();needle='\tmodel = "ASUS';a=s.index(needle);s=s[:a]+'''\tthermal-sensor {
		compatible = "generic-adc-thermal";
		#thermal-sensor-cells = <0>;
		io-channels = <&auxadc 0>;
		io-channel-names = "sensor-channel";
	};

'''+s[a:];s=s.replace('compatible = "ti,lp8557-led";','compatible = "ti,lp8557-led";\n\t\tenable-gpios = <&pio 43 0>;');p.write_text(s)
p=src/'arch/arm64/configs/asus_p00a_defconfig';s=p.read_text();s=re.sub(r'^CONFIG_THERMAL_KARNAK=y\n','',s,flags=re.M);s+='\n# CONFIG_THERMAL_KARNAK is not set\nCONFIG_THERMAL_ASUS_P00A=y\nCONFIG_ASUS_P00A_LP8557=y\n';p.write_text(s)
# Confirm curve 6 is numerically identical before keeping its existing 4.9 copy.
def curve(text):
 x=re.search(r'BTS_Temperature_Table6\[\]\s*=\s*\{(.*?)\};',text,re.S).group(1)
 return [(int(a),int(b)) for a,b in re.findall(r'\{\s*(-?\d+)\s*,\s*(\d+)\s*\}',x)]
a=curve((old/'drivers/misc/mediatek/thermal/mt8163/mtk_ts_bts.c').read_text());b=curve(new)
assert a==b and len(a)==34
(root/'evidence/thermal-curve-verification.json').write_text(json.dumps(dict(status='passed',matched_points=len(a),pull_up_ohm=390000,pull_up_mv=1800,critical_ohm=4251000,ntc_table=6,adc_channel=0,curve=a),indent=2)+'\n')
print('Touch GPIO ownership and ASUS thermistor configuration ported; 34 original NTC points match.')
