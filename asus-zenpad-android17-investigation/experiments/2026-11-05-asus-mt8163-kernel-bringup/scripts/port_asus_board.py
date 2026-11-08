#!/usr/bin/env python3
"""Import evidenced ASUS board/panel sources. No firmware image packaging or device writes."""
import hashlib,json,re
from pathlib import Path
from source_edits import ROOT,SOURCE,replace,write_new
old=ROOT.parent/'2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18'
provenance=[]
def imported(path,target=None):
 target=target or path;data=(old/path).read_bytes();p=SOURCE/target
 assert not p.exists(),target;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 provenance.append(dict(original=str(old/path),target=target,sha256=hashlib.sha256(data).hexdigest()))
 return p
panel='z380m_kd_rm68200g01';folder='drivers/misc/mediatek/lcm/'+panel
for f in ['Makefile',panel+'.c']:imported(folder+'/'+f)
p=SOURCE/(folder+'/'+panel+'.c');s=p.read_text()
s=s.replace('extern int Read_HW_ID(void);\nextern char *lk_lcmname;', 'extern char *mtkfb_find_lcm_driver(void);')
# This import targets the observed production HW_ID=3 unit, not the EVB.
start=s.index('\tif (Read_HW_ID() == 0) { //EVB')
mid=s.index('\t} else {',start);end=s.index('\n\t}',mid)
production=s[mid+len('\t} else {'):end]
production='\n'.join(line[1:] if line.startswith('\t') else line for line in production.split('\n'))
s=s[:start]+production+s[end+len('\n\t}'):]
s=s.replace('static int __init lcm_init(void)\n{','static int __init lcm_init(void)\n{\n\tconst char *panel_name = mtkfb_find_lcm_driver();')
s=s.replace('if (!strcmp(z380m_kd_rm68200g01_lcm_drv.name, lk_lcmname)) {','if (panel_name && !strcmp(z380m_kd_rm68200g01_lcm_drv.name, panel_name)) {')
p.write_text(s)
replace('drivers/misc/mediatek/lcm/mt65xx_lcm_list.h','#include <lcm_drv.h>','#include <lcm_drv.h>\n\nextern struct LCM_DRIVER z380m_kd_rm68200g01_lcm_drv;')
replace('drivers/misc/mediatek/lcm/mt65xx_lcm_list.c','struct LCM_DRIVER *lcm_driver_list[] = {','struct LCM_DRIVER *lcm_driver_list[] = {\n#if defined(Z380M_KD_RM68200G01)\n\t&z380m_kd_rm68200g01_lcm_drv,\n#endif')
# GT6108 shares the coordinate/version/config registers and 240-byte config size
# with this Goodix driver. This is a compile candidate; hardware validation is pending.
replace('drivers/input/touchscreen/goodix.c','static const struct of_device_id goodix_of_match[] = {','static const struct of_device_id goodix_of_match[] = {\n\t{ .compatible = "goodix,gt6108" },')
replace('drivers/input/touchscreen/goodix.c','\tif (ts->gpiod_int && ts->gpiod_rst) {\n\t\t/* update device config */','\tif (ts->gpiod_int && ts->gpiod_rst &&\n\t    !of_device_is_compatible(client->dev.of_node, "goodix,gt6108")) {\n\t\t/* update device config */')
dtsdir='arch/arm64/boot/dts/mediatek/'
p=imported('arch/arm64/boot/dts/asus8163_tb_380_m-Z380M.dts',dtsdir+'asus-p00a.dts')
imported('arch/arm64/boot/dts/asus8163_tb_380_m_bat_setting.dtsi',dtsdir+'asus8163_tb_380_m_bat_setting.dtsi')
s=p.read_text().replace('/ {\n','/ {\n\tmodel = "ASUS ZenPad 8.0 Z380M P00A_2 - compile candidate";\n\tcompatible = "asus,p00a", "mediatek,mt8163";\n',1)
s=s.replace('console=ttyS0,921600n1','console=ttyMT0,921600n1')
# Generic Goodix uses descriptor GPIO names. Keep the original ASUS pinctrl and
# regulator wiring. irq follows the stock controller mapping; runtime is untested.
s=s.replace('compatible = "goodix,gt6108";','compatible = "goodix,gt6108";\n\t\tirq-gpios = <&pio 35 0>;\n\t\treset-gpios = <&pio 45 0>;')
p.write_text(s)
replace(dtsdir+'Makefile','dtb-$(CONFIG_ARCH_MEDIATEK) += mt6755-evb.dtb','dtb-$(CONFIG_ARCH_MEDIATEK) += asus-p00a.dtb\ndtb-$(CONFIG_ARCH_MEDIATEK) += mt6755-evb.dtb')
config=(SOURCE/'arch/arm64/configs/karnak_defconfig').read_text()
changes={
 'ARCH_MTK_PROJECT':'"asus_p00a"',
 'BUILD_ARM64_APPENDED_DTB_IMAGE_NAMES':'"mediatek/asus-p00a"',
 'CUSTOM_KERNEL_LCM':'"z380m_kd_rm68200g01"',
 'TOUCHSCREEN_GTP9XX':None,'TOUCHSCREEN_GOODIX':'y',
 'MTK_IMGSENSOR':None,'CUSTOM_KERNEL_IMGSENSOR':'""',
 'CUSTOM_KERNEL_ACCELEROMETER':None,'CUSTOM_KERNEL_ALSPS':None,'CUSTOM_KERNEL_GYROSCOPE':None,
 # Do not select Amazon chargers for ASUS. This intentionally exposes the still
 # unported ASUS charging interface at link time rather than providing a stub.
 'MTK_BQ24296_SUPPORT':None,'MTK_BQ25601_SUPPORT':None,
 'LOCALVERSION':'"-asus-p00a-experimental"','IKCONFIG':'y','IKCONFIG_PROC':'y',
}
for name,val in changes.items():
 config=re.sub(r'^(?:CONFIG_'+name+r'=.*|# CONFIG_'+name+r' is not set)\n','',config,flags=re.M)
 config+=('# CONFIG_'+name+' is not set\n') if val is None else ('CONFIG_'+name+'='+val+'\n')
write_new('arch/arm64/configs/asus_p00a_defconfig',config)
(ROOT/'evidence/asus-import-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print('Imported evidenced ASUS panel and board; configured generic GT6108 candidate; wrong charger selections disabled.')
