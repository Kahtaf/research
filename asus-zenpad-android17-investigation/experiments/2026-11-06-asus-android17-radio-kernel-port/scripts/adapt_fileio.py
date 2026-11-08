from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]/'stagedpatches/kernel-input/drivers/misc/mediatek/connectivity'
C=R/'common/conn_soc';W=R/'wlan/gen2'
def replace_func(p,name,body):
 s=p.read_text(); m=re.search(r'^(?:INT32|MTK_WCN_BOOL|WLAN_STATUS|static int) '+name+r'\([^;]*?\n\{',s,re.M);assert m,(p,name)
 a=m.start();b=s.index('\n}',m.end())+2;s=s[:a]+body+s[b:];p.write_text(s)
p=C/'linux/pri/wmt_dev.c'
replace_func(p,'wmt_dev_read_file','''INT32 wmt_dev_read_file(PUINT8 pName, const PPUINT8 ppBufPtr, INT32 offset, INT32 padSzBuf)
{
	struct file *file;
	loff_t size;
	unsigned char *buf;
	int ret;

	if (!ppBufPtr || offset < 0 || padSzBuf < 0 || padSzBuf > BCNT_PATCH_BUF_HEADROOM)
		return -EINVAL;
	*ppBufPtr = NULL;
	file = filp_open(pName, O_RDONLY, 0);
	if (IS_ERR(file))
		return PTR_ERR(file);
	size = i_size_read(file_inode(file)) - offset;
	if (size <= 0 || size > INT_MAX - BCNT_PATCH_BUF_HEADROOM - 4) {
		ret = -EINVAL;
		goto close;
	}
	buf = vzalloc(size + BCNT_PATCH_BUF_HEADROOM + 4);
	if (!buf) {
		ret = -ENOMEM;
		goto close;
	}
	/* 4.9 kernel_read supports read_iter-backed filesystems such as ext4. */
	ret = kernel_read(file, offset, buf + padSzBuf, size);
	if (ret != size) {
		vfree(buf);
		if (ret >= 0)
			ret = -EIO;
	} else {
		*ppBufPtr = buf;
	}
close:
	filp_close(file, NULL);
	return ret;
}''')
replace_func(p,'wmt_dev_patch_get','''INT32 wmt_dev_patch_get(PUINT8 pPatchName, osal_firmware **ppPatch, INT32 padSzBuf)
{
	osal_firmware *fw;
	int ret;

	if (!ppPatch || !pPatchName || !*pPatchName)
		return -EINVAL;
	wmt_dev_patch_put(ppPatch);
	fw = kzalloc(sizeof(*fw), GFP_KERNEL);
	if (!fw)
		return -ENOMEM;
	ret = wmt_dev_read_file(pPatchName, (const PPUINT8)&fw->data, 0, padSzBuf);
	if (ret < 0) {
		kfree(fw);
		return ret;
	}
	fw->size = ret;
	*ppPatch = fw;
	return 0;
}''')
replace_func(p,'wmt_dev_is_file_exist','''MTK_WCN_BOOL wmt_dev_is_file_exist(PUINT8 pFileName)
{
	struct file *file;
	bool valid;

	if (!pFileName || !*pFileName)
		return MTK_WCN_BOOL_FALSE;
	file = filp_open(pFileName, O_RDONLY, 0);
	if (IS_ERR(file))
		return MTK_WCN_BOOL_FALSE;
	valid = i_size_read(file_inode(file)) > 0;
	filp_close(file, NULL);
	return valid;
}''')
# Source-visible ARM64 pointer truncations in internal op buffers are not on-wire fields.
for p in C.rglob('*.c'):
 s=p.read_text();s=re.sub(r'\(UINT32\)\s*(&[A-Za-z_][A-Za-z_0-9]*|pData\b)',r'(SIZE_T) \1',s);p.write_text(s)
p=C/'core/wmt_conf.c';s=p.read_text().replace('pBuf = osal_malloc(size);','pBuf = osal_malloc(size + 1);');p.write_text(s)
# Firmware open/load/close no longer mutate shared struct cred or hold set_fs across calls.
p=W/'os/linux/gl_kal.c';s=p.read_text()
s=s.replace('static uid_t orgfsuid;\nstatic gid_t orgfsgid;\nstatic mm_segment_t orgfs;\n','')
a=s.index('\t/* FIX ME: since we don\'t have hotplug script',s.index('WLAN_STATUS kalFirmwareOpen'))
b=s.index('\t/* open the fw file */',a);s=s[:a]+'\tASSERT(prGlueInfo);\n\n'+s[b:]
a=s.index('error_open:',s.index('WLAN_STATUS kalFirmwareOpen'));b=s.index('\n}',a)
s=s[:a]+'error_open:\n\tfilp = NULL;\n\treturn WLAN_STATUS_FAILURE;'+s[b:];p.write_text(s)
replace_func(p,'kalFirmwareClose','''WLAN_STATUS kalFirmwareClose(IN P_GLUE_INFO_T prGlueInfo)
{
	if (!IS_ERR_OR_NULL(filp))
		filp_close(filp, NULL);
	filp = NULL;
	return WLAN_STATUS_SUCCESS;
}''')
replace_func(p,'kalFirmwareLoad','''WLAN_STATUS kalFirmwareLoad(IN P_GLUE_INFO_T prGlueInfo, OUT PVOID prBuf, IN UINT_32 u4Offset, OUT PUINT_32 pu4Size)
{
	int ret;

	if (IS_ERR_OR_NULL(filp) || !prBuf || !pu4Size || *pu4Size > INT_MAX)
		return WLAN_STATUS_FAILURE;
	ret = kernel_read(filp, u4Offset, prBuf, *pu4Size);
	if (ret < 0 || ret != *pu4Size)
		return WLAN_STATUS_FAILURE;
	*pu4Size = ret;
	return WLAN_STATUS_SUCCESS;
}''')
replace_func(p,'kalFirmwareSize','''WLAN_STATUS kalFirmwareSize(IN P_GLUE_INFO_T prGlueInfo, OUT PUINT_32 pu4Size)
{
	loff_t size;

	if (IS_ERR_OR_NULL(filp) || !pu4Size)
		return WLAN_STATUS_FAILURE;
	size = i_size_read(file_inode(filp));
	if (size <= 0 || size > INT_MAX)
		return WLAN_STATUS_FAILURE;
	*pu4Size = size;
	return WLAN_STATUS_SUCCESS;
}''')
# Keep device-local NVRAM locations and contents; fix only the filesystem API.
p=W/'os/linux/platform.c'
s=p.read_text();a=s.index('static int nvram_read(');b=s.index('\n#else /* !CFG_SUPPORT_NVRAM */',a)
head='''static int nvram_read(char *filename, char *buf, ssize_t len, int offset)
{
#if CFG_SUPPORT_NVRAM
	struct file *file;
	int ret;

	if (len < 0 || offset < 0)
		return -EINVAL;
	file = filp_open(filename, O_RDONLY, 0);
	if (IS_ERR(file))
		return PTR_ERR(file);
	ret = kernel_read(file, offset, buf, len);
	filp_close(file, NULL);
	return ret;
''';s=s[:a]+head+s[b:]
# nvram_write remains callable via original ioctl; preserve behavior with real kernel_write.
a=s.index('static int nvram_write(');b=s.index('\n#else /* !CFG_SUPPORT_NVRAMS */',a)
head='''static int nvram_write(char *filename, char *buf, ssize_t len, int offset)
{
#if CFG_SUPPORT_NVRAM
	struct file *file;
	ssize_t ret;

	if (len < 0 || offset < 0)
		return -EINVAL;
	file = filp_open(filename, O_WRONLY, 0);
	if (IS_ERR(file))
		return PTR_ERR(file);
	ret = kernel_write(file, buf, len, offset);
	filp_close(file, NULL);
	return ret;
''';s=s[:a]+head+s[b:];p.write_text(s)
# Correct units at the new cfg80211 API boundary (seconds -> ASUS milliseconds).
p=W/'os/linux/gl_cfg80211.c';s=p.read_text();s=s.replace('request->scan_plans[0].interval > 65535','request->scan_plans[0].interval > 65').replace('(UINT_16) request->scan_plans[0].interval;','(UINT_16) (request->scan_plans[0].interval * 1000);')
a=s.index('int mtk_cfg80211_disconnect');b=s.index('\n}',a)
s=s[:a]+s[a:b].replace('if (rStatus != WLAN_STATUS_SUCCESS) {','if (rStatus != WLAN_STATUS_SUCCESS) {\n\t\tprGlueInfo->p00a_local_disconnect = false;')+s[b:]
a=s.index('int mtk_cfg80211_connect');b=s.index('\n}',a)
s=s[:a]+s[a:b].replace('ASSERT(prGlueInfo);','ASSERT(prGlueInfo);\n\tprGlueInfo->p00a_local_disconnect = false;')+s[b:];p.write_text(s)
p=W/'os/linux/gl_init.c';s=p.read_text().replace('prWiphy->max_sched_scan_ssids\t= CFG_SCAN_SSID_MAX_NUM;','prWiphy->max_sched_scan_ssids\t= CFG_SCAN_SSID_MAX_NUM;\n\tprWiphy->max_sched_scan_plans = 1;\n\tprWiphy->max_sched_scan_plan_interval = 65;');p.write_text(s)
