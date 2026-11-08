from pathlib import Path
p=Path(__file__).resolve().parents[1]/'stagedpatches/kernel-input/drivers/misc/mediatek/connectivity/common/conn_soc/mt8163/mtk_wcn_consys_hw.c'
s=p.read_text();a=s.index('INT32 mtk_wcn_consys_hw_reg_ctrl(');b=s.index('INT32 mtk_wcn_consys_hw_gpio_ctrl(',a)
s=s[:a]+'''/* Exact MT8163/MT6323 sequence from the ASUS path above, with checked
 * regulator/PMIC/reset operations and balanced partial-failure cleanup.
 * scpsys owns the MTCMOS isolation, bus protection and domain clocks.
 */
static bool p00a_vcn18_on, p00a_vcn28_on, p00a_domain_on;

static int p00a_pmic_field(unsigned int reg, unsigned int value,
			    unsigned int mask, unsigned int shift)
{
	int ret;
	pmic_lock();
	ret = pmic_config_interface(reg, value, mask, shift);
	pmic_unlock();
	return ret ? -EIO : 0;
}

static int p00a_vcn28_mode(unsigned int hw)
{
	return p00a_pmic_field(ANALDO_CON19, hw,
		PMIC_VCN28_ON_CTRL_MASK, PMIC_VCN28_ON_CTRL_SHIFT);
}

static int p00a_radio_power_down(void)
{
	int ret = 0, err;

	err = reset_control_assert(rstc);
	if (err) ret = err;
	if (p00a_domain_on) {
		err = mtk_wcn_consys_power_off();
		/* pm_runtime_put_sync consumes the acquired usage reference. */
		p00a_domain_on = false;
		if (!ret) ret = err;
	}
	if (p00a_vcn28_on) {
		err = p00a_vcn28_mode(0);
		if (!ret) ret = err;
		err = regulator_disable(reg_VCN28);
		if (!err) p00a_vcn28_on = false;
		if (!ret) ret = err;
	}
	if (p00a_vcn18_on) {
		err = regulator_disable(reg_VCN18);
		if (!err) p00a_vcn18_on = false;
		if (!ret) ret = err;
	}
	return ret;
}

INT32 mtk_wcn_consys_hw_reg_ctrl(UINT32 on, UINT32 co_clock_type)
{
	int ret;
	unsigned int retry, chip = 0;

	if (!my_pdev)
		return -EPROBE_DEFER;
	if (!on)
		return p00a_radio_power_down();
	if (p00a_domain_on || p00a_vcn18_on || p00a_vcn28_on)
		return -EBUSY;
	ret = p00a_pmic_field(DIGLDO_CON11, 0,
		PMIC_VCN_1V8_LP_MODE_SET_MASK, PMIC_VCN_1V8_LP_MODE_SET_SHIFT);
	if (ret) return ret;
	ret = regulator_set_voltage(reg_VCN18, 1800000, 1800000);
	if (ret) return ret;
	ret = regulator_enable(reg_VCN18);
	if (ret) return ret;
	p00a_vcn18_on = true;
	udelay(150);
	ret = p00a_vcn28_mode(co_clock_type ? 0 : 1);
	if (ret) goto fail;
	if (!co_clock_type) {
		ret = regulator_set_voltage(reg_VCN28, 2800000, 2800000);
		if (ret) goto fail;
		ret = regulator_enable(reg_VCN28);
		if (ret) goto fail;
		p00a_vcn28_on = true;
	}
	ret = reset_control_assert(rstc);
	if (ret) goto fail;
	ret = mtk_wcn_consys_power_on();
	if (ret) goto fail;
	p00a_domain_on = true;
	udelay(10);
	for (retry = 0; retry < 10; retry++) {
		chip = CONSYS_REG_READ(conn_reg.mcu_base + CONSYS_CHIP_ID_OFFSET);
		if (chip == 0x8163) break;
		msleep(20);
	}
	if (chip != 0x8163) { ret = -ETIMEDOUT; goto fail; }
	CONSYS_REG_WRITE(conn_reg.mcu_base + CONSYS_MCU_CFG_ACR_OFFSET,
		CONSYS_REG_READ(conn_reg.mcu_base + CONSYS_MCU_CFG_ACR_OFFSET) |
		CONSYS_MCU_CFG_ACR_MBIST_BIT);
	ret = reset_control_deassert(rstc);
	if (ret) goto fail;
	msleep(20);
	return 0;
fail:
	{
		int cleanup = p00a_radio_power_down();
		if (cleanup)
			WMT_PLAT_ERR_FUNC("power rollback failed: %d\\n", cleanup);
	}
	return ret;
}

'''+s[b:]
s=s.replace('iRet += mtk_wcn_consys_hw_reg_ctrl(1, co_clock_type);\n\tiRet += mtk_wcn_consys_hw_gpio_ctrl(1);','''iRet = mtk_wcn_consys_hw_reg_ctrl(1, co_clock_type);
	if (iRet)
		return iRet;
	iRet = mtk_wcn_consys_hw_gpio_ctrl(1);
	if (iRet) {
		mtk_wcn_consys_hw_gpio_ctrl(0);
		mtk_wcn_consys_hw_reg_ctrl(0, co_clock_type);
		return iRet;
	}''')
s=s.replace('iRet += mtk_wcn_consys_hw_reg_ctrl(0, co_clock_type);\n\n\t/*2. do whole hw power on flow */', 'iRet = mtk_wcn_consys_hw_reg_ctrl(0, co_clock_type);\n\tif (iRet)\n\t\treturn iRet;\n\n\t/*2. do whole hw power on flow */')
# Retain the ASUS single shared 3.3V route through vcn33_bt, with idempotent
# per-function ownership. The reference counter used to swallow enable failures.
a=s.index('#if CONSYS_BT_WIFI_SHARE_V33\nINT32');b=s.index('\n#else\nINT32 mtk_wcn_consys_hw_bt_paldo_ctrl',a)
s=s[:a]+'''#if CONSYS_BT_WIFI_SHARE_V33
static unsigned int p00a_vcn33_users;
static DEFINE_MUTEX(p00a_vcn33_lock);
static int p00a_vcn33_ctrl(unsigned int user, unsigned int enable)
{
	unsigned int next;
	int ret = 0;
	if (!my_pdev) return -EPROBE_DEFER;
	if (enable > 1) return -EINVAL;
	mutex_lock(&p00a_vcn33_lock);
	next = enable ? p00a_vcn33_users | user : p00a_vcn33_users & ~user;
	if (!p00a_vcn33_users && next) {
		ret = regulator_set_voltage(reg_VCN33_BT, 3300000, 3300000);
		if (ret) goto out;
		ret = regulator_enable(reg_VCN33_BT);
		if (ret) goto out;
		ret = p00a_pmic_field(ANALDO_CON16, 1,
			PMIC_VCN33_ON_CTRL_BT_MASK, PMIC_VCN33_ON_CTRL_BT_SHIFT);
		if (ret) {
			regulator_disable(reg_VCN33_BT);
			goto out;
		}
	} else if (p00a_vcn33_users && !next) {
		ret = p00a_pmic_field(ANALDO_CON16, 0,
			PMIC_VCN33_ON_CTRL_BT_MASK, PMIC_VCN33_ON_CTRL_BT_SHIFT);
		if (ret) goto out;
		ret = regulator_disable(reg_VCN33_BT);
		if (ret) goto out;
	}
	p00a_vcn33_users = next;
out:
	mutex_unlock(&p00a_vcn33_lock);
	return ret;
}
INT32 mtk_wcn_consys_hw_bt_paldo_ctrl(UINT32 enable)
{
	return p00a_vcn33_ctrl(1, enable);
}
INT32 mtk_wcn_consys_hw_wifi_paldo_ctrl(UINT32 enable)
{
	return p00a_vcn33_ctrl(2, enable);
}
'''+s[b:]
p.write_text(s)
