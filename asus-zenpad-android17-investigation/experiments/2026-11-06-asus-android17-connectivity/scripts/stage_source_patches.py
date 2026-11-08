#!/usr/bin/env python3
"""Save narrowly selected GPL evidence and generate a firmware-path patch."""
import difflib, hashlib, json, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
ORIGINAL=ROOT.parent/'2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18'
PREFIX='drivers/misc/mediatek/connectivity/'
FILES=[
 'Makefile','common/Makefile','common/conn_soc/Makefile',
 'common/conn_soc/linux/pub/Makefile', 'common/common_detect/Makefile',
 'common/conn_soc/linux/pri/wmt_dev.c',
 'common/conn_soc/linux/pub/stp_chrdev_bt.c',
 'common/conn_soc/linux/pub/wmt_chrdev_wifi.c',
 'common/conn_soc/core/wmt_ic_soc.c',
 'common/conn_soc/core/wmt_conf.c',
 'common/conn_soc/core/include/wmt_conf.h',
 'common/conn_soc/core/include/wmt_lib.h',
 'common/conn_soc/linux/pub/include/stp_chrdev_bt.h',
 'wlan/Makefile','wlan/gen2/Makefile','wlan/gen2/os/linux/platform.c',
 'wlan/gen2/os/linux/gl_wext_priv.c','wlan/gen2/os/linux/gl_init.c',
 'wlan/gen2/os/linux/gl_kal.c', 'wlan/gen2/include/CFG_Wifi_File.h',
]
manifest={}
for f in FILES:
 p=ORIGINAL/(PREFIX+f)
 if not p.exists(): continue
 dest=ROOT/'sources/asus-gpl/kernel-3.18'/(PREFIX+f)
 dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(p.read_bytes())
 manifest[str(p.relative_to(ROOT.parent))]={'local':str(dest.relative_to(ROOT)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for f in ['COPYING','arch/arm64/configs/asus8163_tb_380_m_defconfig']:
 p=ORIGINAL/f; dest=ROOT/'sources/asus-gpl/kernel-3.18'/f
 dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(p.read_bytes())
 manifest[str(p.relative_to(ROOT.parent))]={'local':str(dest.relative_to(ROOT)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
patch=''
for f,old,new in [
 ('common/conn_soc/core/include/wmt_conf.h','/system/etc/firmware/','/vendor/firmware/'),
 ('wlan/gen2/os/linux/gl_kal.c','/etc/firmware/','/vendor/firmware/'),
]:
 rel=PREFIX+f
 before=(ORIGINAL/rel).read_text()
 after=before.replace(old,new)
 assert before!=after
 patch+=''.join(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='a/'+rel,tofile='b/'+rel))
 dest=ROOT/'staged/asus-gpl-patched'/rel
 dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(after)
patchdir=ROOT/'staged/patches';patchdir.mkdir(parents=True,exist_ok=True)
(patchdir/'0001-asus-gpl-use-vendor-firmware.patch').write_text(patch)
(ROOT/'evidence/local-source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Captured',len(manifest),'GPL source files; generated firmware path patch (not a 4.9 port)')
# The stock published BT handler uses pointer-sized ioctl encodings but forwards
# 32-bit requests unchanged. Translate only the three known size-varying commands.
rel=PREFIX+'common/conn_soc/linux/pub/stp_chrdev_bt.c'
before=(ORIGINAL/rel).read_text()
needle='#define COMBO_IOC_MAGIC             0xb0'
assert before.count(needle)==1
after=before.replace(needle,'#ifdef CONFIG_COMPAT\n#include <linux/compat.h>\n#endif\n\n'+needle)
needle='''long BT_compat_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{
	return BT_unlocked_ioctl(filp, cmd, arg);
}'''
replacement='''long BT_compat_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{
#ifdef CONFIG_COMPAT
	/* ioctl numbers include sizeof(void *); ARM clients encode four bytes. */
	switch (cmd) {
	case _IOWR(COMBO_IOC_MAGIC, 1, compat_uptr_t):
		cmd = COMBO_IOCTL_BT_IC_HW_VER;
		break;
	case _IOWR(COMBO_IOC_MAGIC, 2, compat_uptr_t):
		cmd = COMBO_IOCTL_BT_IC_FW_VER;
		break;
	case _IOWR(COMBO_IOC_MAGIC, 3, compat_uptr_t):
		cmd = COMBO_IOC_BT_HWVER;
		arg = (unsigned long)compat_ptr(arg);
		break;
	}
#endif
	return BT_unlocked_ioctl(filp, cmd, arg);
}'''
assert after.count(needle)==1
after=after.replace(needle,replacement)
patch=''.join(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='a/'+rel,tofile='b/'+rel))
(patchdir/'0002-asus-gpl-bt-compat-ioctl-width.patch').write_text(patch)
dest=ROOT/'staged/asus-gpl-patched'/rel
dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(after)
print('Generated BT compat ioctl patch; PSM ioctl is intentionally not implemented')
