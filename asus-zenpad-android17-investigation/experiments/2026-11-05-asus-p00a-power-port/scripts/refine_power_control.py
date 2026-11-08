#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1];d=root/'sources/kernel/drivers/misc/mediatek/power/mt8163/asus_p00a'
p=d/'policy.h';s=p.read_text().replace('bool battery_present;','bool battery_present;\n\tbool charger_present;').replace('p->battery_present && p->sensors_valid &&','p->battery_present && p->charger_present && p->sensors_valid &&')
a=s.index('static inline bool p00a_fault_blocks')
s=s[:a]+'''static inline int p00a_hv_code(unsigned int uv)
{
	static const unsigned int levels[] = {
		4200000, 4250000, 4300000, 4350000,
		4400000, 4450000, 4500000, 4550000,
		4600000, 6000000, 6500000
	};
	int i;

	if (uv < levels[0])
		return -ERANGE;
	for (i = 10; i > 0; i--)
		if (levels[i] <= uv)
			return i;
	return 0;
}

'''+s[a:];p.write_text(s)
p=d/'bq25896.c';s=p.read_text().replace('unsigned int error_state;','unsigned int error_state;\n\tint programmed_cv;\n\tbool initialized;\n\tbool needs_programming;')
s=s.replace('if (!of_machine_is_compatible("asus,p00a"))','if (!of_machine_is_compatible("asus,p00a"))')
p.write_text(s)
p=d/'control.h';s=p.read_text().replace('previous, fault_now, ts;','previous, fault_now, ts, status;')
s=s.replace('ret = regmap_read(p->map, REG_FAULT, &previous);','ret = regmap_read(p->map, REG_STATUS, &status);\n\tif (ret)\n\t\treturn ret;\n\tp->limits.charger_present = !!(status & BIT(2));\n\tif (!p->limits.charger_present) {\n\t\tp->limits.input_cap_ma = 100;\n\t\tp->limits.enable_requested = false;\n\t\tp->needs_programming = true;\n\t}\n\tret = regmap_read(p->map, REG_FAULT, &previous);',1)
a=s.index('static int p00a_apply(');b=s.index('static int p00a_hw_init(',a)
s=s[:a]+'''static int p00a_apply(struct p00a_power *p)
{
	int cv, input, ret, stop_ret;

	if (!p->initialized)
		return -EAGAIN;
	ret = p00a_sample(p);
	if (ret)
		goto stop;
	if (!p00a_can_charge(&p->limits)) {
		ret = p->limits.enable_requested ? -EAGAIN : 0;
		goto stop;
	}
	cv = p00a_effective_cv(&p->limits);
	input = p00a_input_code(p->limits.input_10ua, p->limits.input_cap_ma);
	if (p->programmed_cv != cv)
		p->needs_programming = true;
	if (p->needs_programming) {
		ret = p00a_disable(p);
		if (ret)
			return ret;
		ret = regmap_update_bits(p->map, REG_CV, 0xfc, cv << 2);
		if (ret)
			goto stop;
		ret = regmap_update_bits(p->map, REG_ICHG, 0x7f,
			p00a_ichg_code(p->limits.ichg_10ua));
		if (ret)
			goto stop;
		ret = regmap_update_bits(p->map, REG_INPUT, 0xbf, input);
		if (ret)
			goto stop;
		p->programmed_cv = cv;
		p->needs_programming = false;
	}
	ret = regmap_update_bits(p->map, REG_CONTROL, CHG_ENABLE, CHG_ENABLE);
	if (!ret)
		return 0;
stop:
	p->needs_programming = true;
	stop_ret = p00a_disable(p);
	return stop_ret ? stop_ret : ret;
}

'''+s[b:]
s=s.replace('static int p00a_hw_init(struct p00a_power *p)\n{\n\tint ret;','static int p00a_hw_init(struct p00a_power *p)\n{\n\tint ret;\n\n\tif (p->initialized)\n\t\treturn 0;')
s=s.replace('REG_TIMER, 0xb0, BIT(7) | BIT(3)','REG_TIMER, 0xb8, BIT(7) | BIT(3)')
s=s.replace('REG_ADC, 0x42, BIT(6)','REG_ADC, 0x53, BIT(6)')
s=s.replace('return regmap_update_bits(p->map, REG_INPUT, 0x7f, BIT(6) | 8);','ret = regmap_update_bits(p->map, 0x01, 0x1f, 7);\n\tif (ret)\n\t\treturn ret;\n\tret = regmap_update_bits(p->map, REG_INPUT, 0x7f, BIT(6));\n\tif (!ret) {\n\t\tp->initialized = true;\n\t\tp->needs_programming = true;\n\t}\n\treturn ret;')
s=s.replace('p->limits.cv_uv = value;','p->limits.cv_uv = value;\n\t\tp->needs_programming = true;')
s=s.replace('p->limits.ichg_10ua = *(unsigned int *)data;','p->limits.ichg_10ua = *(unsigned int *)data;\n\t\tp->needs_programming = true;')
s=s.replace('p->limits.input_10ua = *(unsigned int *)data;','p->limits.input_10ua = *(unsigned int *)data;\n\t\tp->needs_programming = true;')
s=s.replace('p->limits.input_cap_ma = p00a_input_cap(value);','p->limits.input_cap_ma = p00a_input_cap(value);\n\t\tp->needs_programming = true;')
s=s.replace('case CHARGING_CMD_GET_HV_STATUS:','case CHARGING_CMD_SET_HV_THRESHOLD:\n\t\tret = p00a_hv_code(*(unsigned int *)data);\n\t\tif (ret < 0)\n\t\t\treturn ret;\n\t\tupmu_set_rg_vcdt_hv_vth(ret);\n\t\treturn 0;\n\tcase CHARGING_CMD_GET_HV_STATUS:')
p.write_text(s)
p=root/'tests/power_control_test.c';s=p.read_text().replace('bool initialized, needs_programming;','bool initialized, needs_programming;\n\tint programmed_cv;').replace('.needs_programming = true }','.needs_programming = true, .initialized = true }').replace('m->r[REG_TS] = 0x47;','m->r[REG_TS] = 0x47;\n\tm->r[REG_STATUS] = 0x16;').replace('.sensors_valid=true,.battery_present=true,','.sensors_valid=true,.battery_present=true,.charger_present=true,').replace('CHECK(p00a_command(&p,CHARGING_CMD_INIT,NULL)==0);','p.initialized=false;\n\tCHECK(p00a_command(&p,CHARGING_CMD_INIT,NULL)==0);')
p.write_text(s)
