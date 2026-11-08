from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]/'stagedpatches/kernel-input/drivers/misc/mediatek/connectivity'
C=R/'common/conn_soc'; W=R/'wlan/gen2'
def edit(p,old,new):
 s=p.read_text(); assert old in s,(p,old);p.write_text(s.replace(old,new))
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
# Opt-in built-in configuration. Reuse actual connadp; never include old common_detect stub.
with (R/'Kconfig').open('a') as f:f.write('''
config ASUS_P00A_RADIO
	bool "ASUS P00A MT8163 WMT/STP and AHB gen2 WLAN port"
	depends on ARM64 && OF && MTK_COMBO=y && MTK_COMBO_CHIP_CONSYS_8163
	depends on MTK_BTIF=y && MTK_COMBO_WIFI=y && MTK_COMBO_BT=y
	depends on CFG80211=y && PM && PM_GENERIC_DOMAINS && RESET_CONTROLLER
	depends on MTK_EMI_MPU && PM_WAKELOCKS
	select CRC16
	select CRC32
	select ZLIB_DEFLATE
	select ZLIB_INFLATE
	help
	  Built-in ASUS GPL transport port for the exact P00A platform.
	  Registers WMT, BT character transport and gen2 AHB WLAN in order.
	  Requires the matching userspace firmware command protocol. No radios
	  are claimed operational merely because this option builds.
''')
edit(R/'Makefile','    # Do Nothing, move to standalone repo','''    obj-$(CONFIG_ASUS_P00A_RADIO) += p00a/
    # Existing adapter remains the owner of reserved memory/platform exports.''')
# Use copied source in place, with one Kbuild directory driving explicitly selected files.
write(R/'p00a/Makefile','''# SPDX-License-Identifier: GPL-2.0-only
subdir-ccflags-y += -DMTK_WCN_REMOVE_KERNEL_MODULE -DMTK_WCN_BUILT_IN_DRIVER
subdir-ccflags-y += -DCONFIG_MTK_WCN_ARM64 -DWMT_PLAT_ALPS=1 -DWMT_IDC_SUPPORT=0
subdir-ccflags-y += -DWMT_CREATE_NODE_DYNAMIC=1
obj-y += ../common/conn_soc/ ../wlan/gen2/ bootstrap.o
''')
# Flags in sibling directory recursion do not inherit from p00a reliably in Kbuild;
# the enclosing connectivity directory is the scope for shared flags.
edit(R/'Makefile','    obj-$(CONFIG_ASUS_P00A_RADIO) += p00a/','''ifeq ($(CONFIG_ASUS_P00A_RADIO),y)
    subdir-ccflags-y += -DMTK_WCN_REMOVE_KERNEL_MODULE -DMTK_WCN_BUILT_IN_DRIVER
    subdir-ccflags-y += -DCONFIG_MTK_WCN_ARM64 -DWMT_PLAT_ALPS=1 -DWMT_IDC_SUPPORT=0
    subdir-ccflags-y += -DWMT_CREATE_NODE_DYNAMIC=1
    obj-y += common/conn_soc/ wlan/gen2/ p00a/
endif''')
write(R/'p00a/Makefile','# SPDX-License-Identifier: GPL-2.0-only\nobj-y += bootstrap.o\n')
# Avoid original abstract export table: direct WMT/STP functions are real linked implementations.
edit(C/'mt8163/Makefile','subdir-ccflags-y += -D MTK_WCN_WMT_STP_EXP_SYMBOL_ABSTRACT','')
# Correct include locations in current platform and connadp headers.
with (C/'Makefile').open('a') as f:f.write('''
subdir-ccflags-y += -I$(srctree)/drivers/misc/mediatek/connectivity/common
subdir-ccflags-y += -I$(srctree)/drivers/misc/mediatek/include/mt-plat/mt8163/include/mach
''')
# Current headers use enum tags, not old typedef aliases.
replacements={'CMB_STUB_AIF_X':'enum CMB_STUB_AIF_X','CMB_STUB_AIF_CTRL':'enum CMB_STUB_AIF_CTRL','COMBO_IF':'enum COMBO_IF','ENUM_BTIF_DPIDLE_CTRL':'enum _ENUM_BTIF_DPIDLE_','ENUM_BTIF_LPBK_MODE':'enum _ENUM_BTIF_LPBK_MODE_','ENUM_BTIF_DBG_ID':'enum _ENUM_BTIF_DBG_ID_'}
for p in C.rglob('*'):
 if p.suffix in ['.c','.h']:
  s=p.read_text()
  for old,new in replacements.items():s=re.sub(r'\b'+old+r'\b',new,s)
  p.write_text(s)
# Shared EMI reservation belongs to connadp, initialized at reservedmem setup.
p=C/'mt8163/mtk_wcn_consys_hw.c'
edit(p,'#include <asm/memblock.h>','#include <linux/memblock.h>')
edit(p,'phys_addr_t gConEmiPhyBase;','extern phys_addr_t gConEmiPhyBase;\nextern unsigned long long gConEmiSize;')
s=p.read_text();start=s.index('/*Reserved memory by device tree!*/');end=s.index('INT32 mtk_wcn_consys_hw_init',start);s=s[:start]+s[end:];p.write_text(s)
# Real CCF/regulator/reset platform: propagate probe failure, no ERR_PTR power use.
edit(p,'regulator_get(&pdev->dev,','devm_regulator_get(&pdev->dev,')
for rail in ['VCN18','VCN28','VCN33_BT','VCN33_WIFI']:
 old='ret = PTR_ERR(reg_'+rail+');'
 edit(p,old,old+'\n\t\treturn ret;')
edit(p,'pm_runtime_enable(&pdev->dev);\n\tmy_pdev = pdev;','')
# Set only when all resources were obtained; use deferred probe safely.
needle='\treturn 0;\n}\n\nstatic INT32 mtk_wmt_remove'
edit(p,needle,'\tpm_runtime_enable(&pdev->dev);\n\tmy_pdev = pdev;\n\treturn 0;\n}\n\nstatic INT32 mtk_wmt_remove')
edit(p,'pm_runtime_disable(&pdev->dev);','pm_runtime_disable(&pdev->dev);\n\tmy_pdev = NULL;')
edit(p,'\tUINT32 retry = 10;','\tUINT32 retry = 10;\n\tif (!my_pdev)\n\t\treturn -EPROBE_DEFER;')
# Kernel reset API may return an error; propagate it.
edit(p,'\t\treset_control_reset(rstc);','\t\t{\n\t\t\tint ret = reset_control_reset(rstc);\n\t\t\tif (ret)\n\t\t\t\treturn ret;\n\t\t}')
# Validate retained reservation before remap instead of overwriting failure with driver registration.
edit(p,'\tnode = of_find_compatible_node(NULL, NULL, "mediatek,mt8163-consys");','''	if (!gConEmiPhyBase || gConEmiSize < SZ_1M)
		return -ENODEV;
	node = of_find_compatible_node(NULL, NULL, "mediatek,mt8163-consys");''')
edit(p,'\tiRet = platform_driver_register(&mtk_wmt_dev_drv);','''	if (!pEmibaseaddr)
		return -ENOMEM;
	iRet = platform_driver_register(&mtk_wmt_dev_drv);''')
# Register thermal callback via current platform bridge. Original STP deep-idle is retained directly.
p=C/'mt8163/wmt_plat_alps.c'
edit(p,'#include <mtk_wcn_cmb_stub.h>','#include <mtk_wcn_cmb_stub.h>\n#include "wmt_build_in_adapter.h"')
s=p.read_text();start=s.index('INT32 wmt_plat_init(')
s=s[:start]+'''static int p00a_thermal_query(void)
{
	return (int)wmt_plat_thermal_ctrl();
}

int mt_combo_plt_enter_deep_idle(enum COMBO_IF src)
{
	if (src != COMBO_IF_BTIF)
		return -EOPNOTSUPP;
	return wmt_plat_deep_idle_ctrl(1);
}

int mt_combo_plt_exit_deep_idle(enum COMBO_IF src)
{
	if (src != COMBO_IF_BTIF)
		return -EOPNOTSUPP;
	return wmt_plat_deep_idle_ctrl(0);
}

int mtk_wcn_wmt_chipid_query(void)
{
	/* Platform identity; analog die/ROM revisions still come from WMT commands. */
	return wmt_plat_get_soc_chipid();
}

'''+s[start:]
s=s.replace('CMB_STUB_CB stub_cb;','struct wmt_platform_bridge bridge = {\n\t\t.thermal_query_cb = p00a_thermal_query,\n\t};')
a=s.index('\tstub_cb.aif_ctrl_cb');b=s.index('#ifdef CFG_WMT_WAKELOCK_SUPPORT',a)
s=s[:a]+'\tiret = 0;\n'+s[b:]
s=s.replace('iret = mtk_wcn_cmb_stub_unreg();','wmt_export_platform_bridge_unregister();')
s=s.replace('iret += mtk_wcn_consys_hw_init();','iret = mtk_wcn_consys_hw_init();\n\tif (!iret)\n\t\twmt_export_platform_bridge_register(&bridge);')
a=s.index('INT32 wmt_plat_init(');b=s.index('EXPORT_SYMBOL(wmt_plat_init)',a)
s=s[:a]+s[a:b].replace('return 0;','return iret;')+s[b:]
# pinctrl functions return error pointers, not NULL. Propagate state-selection failures.
for name in ['consys_pinctrl','gps_lna_init','gps_lna_oh','gps_lna_ol']:
 s=s.replace('NULL == '+name,'IS_ERR_OR_NULL('+name+')')
for name in ['gps_lna_init','gps_lna_oh','gps_lna_ol']:
 s=s.replace('pinctrl_select_state(consys_pinctrl, '+name+');','return pinctrl_select_state(consys_pinctrl, '+name+');')
p.write_text(s)
# Existing BTIF operation really returns an error. Do not swallow it.
p=C/'linux/pri/stp_btif.c'
edit(p,'\t\tmtk_wcn_btif_dpidle_ctrl(stpBtifId, en_flag);','\t\tiRet = mtk_wcn_btif_dpidle_ctrl(stpBtifId, en_flag);')
# GNU kernel include spelling changed; no replacement implementation.
for p in C.rglob('*.h'):
 s=p.read_text().replace('<asm/memblock.h>','<linux/memblock.h>');p.write_text(s)
# WLAN fixed MT8163 bus selection, retain complete MAC/management implementation.
edit(W/'Makefile','$(HIF_DIR)$(MTK_PLATFORM)/ahb_pdma.o','$(HIF_DIR)mt8163/ahb_pdma.o')
with (W/'Makefile').open('a') as f:f.write('''
ccflags-y += -I$(srctree)/drivers/misc/mediatek/include/mt-plat/mt8163/include
''')
write(R/'p00a/bootstrap.c','''// SPDX-License-Identifier: GPL-2.0-only
#include <linux/init.h>
#include <linux/errno.h>
#include <linux/of.h>
#include <linux/printk.h>

extern int mtk_wcn_soc_common_drv_init(void);
extern void mtk_wcn_soc_common_drv_exit(void);
extern int mtk_wcn_stpbt_drv_init(void);
extern void mtk_wcn_stpbt_drv_exit(void);
extern int mtk_wcn_wmt_wifi_init(void);
extern void mtk_wcn_wmt_wifi_exit(void);
extern int mtk_wcn_wlan_gen2_init(void);

static int __init p00a_radio_init(void)
{
	struct device_node *np;
	int ret;

	np = of_find_compatible_node(NULL, NULL, "mediatek,mt8163-consys");
	if (!np)
		return -ENODEV;
	ret = of_device_is_available(np) ? 0 : -ENODEV;
	of_node_put(np);
	if (ret)
		return ret;
	ret = mtk_wcn_soc_common_drv_init();
	if (ret)
		return ret;
	ret = mtk_wcn_stpbt_drv_init();
	if (ret)
		goto common_exit;
	ret = mtk_wcn_wmt_wifi_init();
	if (ret)
		goto bt_exit;
	ret = mtk_wcn_wlan_gen2_init();
	if (ret)
		goto wifi_exit;
	pr_info("p00a-radio: transports registered; firmware launcher required\\n");
	return 0;
wifi_exit:
	mtk_wcn_wmt_wifi_exit();
bt_exit:
	mtk_wcn_stpbt_drv_exit();
common_exit:
	mtk_wcn_soc_common_drv_exit();
	return ret;
}
late_initcall(p00a_radio_init);
''')
