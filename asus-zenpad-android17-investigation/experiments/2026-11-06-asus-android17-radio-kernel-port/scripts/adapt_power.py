from pathlib import Path
import re
C=Path(__file__).resolve().parents[1]/'stagedpatches/kernel-input/drivers/misc/mediatek/connectivity/common/conn_soc'
p=C/'mt8163/mtk_wcn_consys_hw.c';s=p.read_text()
a=s.index('VOID mtk_wcn_consys_power_on(');b=s.index('INT32 mtk_wcn_consys_hw_reg_ctrl(',a)
s=s[:a]+'''static int mtk_wcn_consys_power_on(void)
{
	int ret;

	if (!my_pdev)
		return -EPROBE_DEFER;
	ret = pm_runtime_get_sync(&my_pdev->dev);
	if (ret < 0) {
		pm_runtime_put_noidle(&my_pdev->dev);
		return ret;
	}
	ret = device_init_wakeup(&my_pdev->dev, true);
	if (ret)
		pm_runtime_put_sync(&my_pdev->dev);
	return ret;
}

static int mtk_wcn_consys_power_off(void)
{
	int ret, wake_ret;

	if (!my_pdev)
		return -EPROBE_DEFER;
	ret = pm_runtime_put_sync(&my_pdev->dev);
	wake_ret = device_init_wakeup(&my_pdev->dev, false);
	return ret < 0 ? ret : wake_ret;
}

'''+s[b:]
s=s.replace('UINT32 retry = 10;\n\tif (!my_pdev)\n\t\treturn -EPROBE_DEFER;\n\tUINT32 consysHwChipId = 0;', 'UINT32 retry = 10;\n\tUINT32 consysHwChipId = 0;\n\tint ret;\n\n\tif (!my_pdev)\n\t\treturn -EPROBE_DEFER;')
s=s.replace('mtk_wcn_consys_power_on();','''ret = mtk_wcn_consys_power_on();
		if (ret)
			return ret;''')
s=s.replace('mtk_wcn_consys_power_off();','''ret = mtk_wcn_consys_power_off();
		if (ret)
			return ret;''')
# Avoid success on exhausted/underflowed polling counter. Timeout must abort WMT.
s=s.replace('if ((0 == retry) || (0 == consysHwChipId)) {','''if (consysHwChipId != 0x8163 && consysHwChipId != 0x0321 &&
		    consysHwChipId != 0x0335 && consysHwChipId != 0x0337) {''')
needle='\n\t\t/*13.{default no need}update ROMDEL/PATCH RAM DELSEL if needed 0x18070114 */'
idx=s.index(needle);end=s.rfind('\n\t\t}',0,idx)
s=s[:end]+'''\n			mtk_wcn_consys_hw_reg_ctrl(0, co_clock_type);
			return -ETIMEDOUT;'''+s[end:]
# Acquire of_node ref once, verify mapped resources and release it.
needle='\n\tif (gConEmiPhyBase) {'
a=s.index('INT32 mtk_wcn_consys_hw_init');idx=s.index(needle,a)
s=s[:idx]+'''
	of_node_put(node);
	if (!conn_reg.mcu_base || !conn_reg.topckgen_base)
		return -ENOMEM;
'''+s[idx:]
p.write_text(s)
