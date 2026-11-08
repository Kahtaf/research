#!/usr/bin/env python3
"""Use a checked read-only FD snapshot instead of kernel pathname calibration I/O."""
from pathlib import Path
import json,hashlib,difflib,shutil
R=Path('/srv/android/asus-build-continuation');K=R/'kernel';D=R/'product-device';changes={};diff=[]
assert (R/'logs/kernel-r2.exit-code').read_text().strip()=='0'
assert not (R/'evidence/wifi-snapshot-fix.json').exists()
def put(p,new):
 old=p.read_text() if p.exists() else '';assert old!=new;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(new)
 changes[str(p)]={'before':hashlib.sha256(old.encode()).hexdigest() if old else None,'after':hashlib.sha256(new.encode()).hexdigest()}
 diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+str(p.relative_to(R)),tofile='b/'+str(p.relative_to(R))))
header='''/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef _LINUX_ASUS_P00A_RADIO_H
#define _LINUX_ASUS_P00A_RADIO_H
#include <linux/types.h>
int p00a_wifi_nvram_load_fd(unsigned int fd);
bool p00a_wifi_nvram_ready(void);
int p00a_read_wifi_nvram(void *buffer, size_t length);
#endif
'''
put(K/'include/linux/asus_p00a_radio.h',header)
p=K/'drivers/misc/mediatek/connectivity/wlan/gen2/os/linux/platform.c';s=p.read_text();s=s.replace('#include <linux/fs.h>','#include <linux/fs.h>\n#include <linux/file.h>\n#include <linux/mutex.h>\n#include <linux/etherdevice.h>\n#include <linux/asus_p00a_radio.h>')
s=s.replace('#define WIFI_NVRAM_FILE_NAME   "/data/vendor/p00a/nvram/APCFG/APRDEB/WIFI"\n#define WIFI_NVRAM_CUSTOM_NAME "/data/vendor/p00a/nvram/APCFG/APRDEB/WIFI_CUSTOM"\n','')
start=s.index('static int nvram_read(');end=s.index('\n}',s.index('BOOLEAN kalCfgDataWrite16(',start))+2
replacement='''static DEFINE_MUTEX(p00a_nvram_lock);
static WIFI_CFG_PARAM_STRUCT p00a_nvram_snapshot;
static bool p00a_nvram_valid;

int p00a_wifi_nvram_load_fd(unsigned int fd)
{
	WIFI_CFG_PARAM_STRUCT candidate;
	struct file *file;
	ssize_t n;
	int ret = 0;

	BUILD_BUG_ON(sizeof(candidate) != 512);
	file = fget(fd);
	if (!file)
		return -EBADF;
	if (!(file->f_mode & FMODE_READ) || (file->f_mode & FMODE_WRITE) ||
	    !S_ISREG(file_inode(file)->i_mode) ||
	    i_size_read(file_inode(file)) != sizeof(candidate) + 2) {
		fput(file);
		return -EINVAL;
	}
	/* Read the logical prefix only. Never modify the full 514-byte container.
	 * This syscall still runs in the vendor loader's security domain. */
	n = kernel_read(file, 0, (char *)&candidate, sizeof(candidate));
	if (i_size_read(file_inode(file)) != sizeof(candidate) + 2)
		ret = -ESTALE;
	fput(file);
	if (ret)
		return ret;
	if (n != sizeof(candidate))
		return n < 0 ? n : -EIO;
	if (!is_valid_ether_addr(candidate.aucMacAddress) || !candidate.ucTxPwrValid)
		return -EINVAL;
	mutex_lock(&p00a_nvram_lock);
	/* Once installed, calibration cannot change until the next boot. */
	if (p00a_nvram_valid) {
		if (memcmp(&p00a_nvram_snapshot, &candidate, sizeof(candidate)))
			ret = -EBUSY;
	} else {
		memcpy(&p00a_nvram_snapshot, &candidate, sizeof(candidate));
		p00a_nvram_valid = true;
	}
	mutex_unlock(&p00a_nvram_lock);
	return ret;
}

bool p00a_wifi_nvram_ready(void)
{
	bool ready;
	mutex_lock(&p00a_nvram_lock);
	ready = p00a_nvram_valid;
	mutex_unlock(&p00a_nvram_lock);
	return ready;
}

int p00a_read_wifi_nvram(void *buffer, size_t length)
{
	int ret = 0;
	if (!buffer || length != sizeof(p00a_nvram_snapshot))
		return -EINVAL;
	mutex_lock(&p00a_nvram_lock);
	if (!p00a_nvram_valid)
		ret = -ENODATA;
	else
		memcpy(buffer, &p00a_nvram_snapshot, length);
	mutex_unlock(&p00a_nvram_lock);
	return ret;
}

BOOLEAN kalCfgDataRead16(IN P_GLUE_INFO_T prGlueInfo, IN UINT_32 u4Offset, OUT PUINT_16 pu2Data)
{
	bool ready;
	if (!pu2Data || u4Offset > sizeof(p00a_nvram_snapshot) - sizeof(*pu2Data))
		return FALSE;
	mutex_lock(&p00a_nvram_lock);
	ready = p00a_nvram_valid;
	if (ready)
		memcpy(pu2Data, (char *)&p00a_nvram_snapshot + u4Offset, sizeof(*pu2Data));
	mutex_unlock(&p00a_nvram_lock);
	return ready ? TRUE : FALSE;
}

BOOLEAN kalCfgDataWrite16(IN P_GLUE_INFO_T prGlueInfo, UINT_32 u4Offset, UINT_16 u2Data)
{
	/* Factory-record writes are unsupported, never acknowledged as success. */
	return FALSE;
}'''
s=s[:start]+replacement+s[end:];put(p,s)
p=K/'drivers/misc/mediatek/connectivity/p00a/bootstrap.c';s=p.read_text().replace('#include <linux/printk.h>','#include <linux/printk.h>\n#include <linux/asus_p00a_radio.h>');s=s.replace('#define DO_MODULE_INIT _IOR(\'w\', 4, int)',"#define DO_MODULE_INIT _IOR('w', 4, int)\n/* Like the existing commands, the argument is scalar, not a user pointer. */\n#define SET_WIFI_NVRAM_FD _IOW('w', 5, int)")
s=s.replace('\tcase DO_MODULE_INIT:', '''	case SET_WIFI_NVRAM_FD:
		if (!uid_eq(current_euid(), GLOBAL_ROOT_UID))
			return -EPERM;
		if (arg > INT_MAX)
			return -EBADF;
		return p00a_wifi_nvram_load_fd((unsigned int)arg);
	case DO_MODULE_INIT:''')
s=s.replace('\t\tif (arg != P00A_CHIP_ID)\n\t\t\treturn -ENODEV;', '\t\tif (arg != P00A_CHIP_ID)\n\t\t\treturn -ENODEV;\n\t\tif (!p00a_wifi_nvram_ready())\n\t\t\treturn -ENODATA;')
s=s.replace('All three commands encode sizeof(int), and carry scalar arguments.','All commands encode sizeof(int), and carry scalar arguments.');put(p,s)
p=D/'radio/src/wmt_protocol.h';s=p.read_text();needle='#define P00A_LOAD';line=next(x for x in s.splitlines() if x.startswith(needle));s=s.replace(line,line+"\n#define P00A_WIFI_NVRAM_FD _IOW('w', 5, int)");put(p,s)
p=D/'radio/src/p00a_wmt.c';s=p.read_text();at=s.index('static int load(void)');helper='''/* The kernel validates and snapshots this read-only whole-container FD.
 * Its WLAN worker subsequently consumes memory, without crossing /data domains. */
static int stage_wifi_record(int detect_fd)
{
    int fd = open("/data/vendor/p00a/nvram/APCFG/APRDEB/WIFI", O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd < 0) return -errno;
    int ret = do_ioctl(&detect_fd, P00A_WIFI_NVRAM_FD, (uintptr_t)fd);
    close(fd);
    return ret;
}
''';s=s[:at]+helper+s[at:];s=s.replace('if (ret == 0x8163) ret = do_ioctl(&fd, P00A_LOAD, 0x8163);','if (ret == 0x8163) {\n        ret = stage_wifi_record(fd);\n        if (!ret) ret = do_ioctl(&fd, P00A_LOAD, 0x8163);\n    }')
start=s.index('    unsigned char record[512];',s.index('static int wifi_on(void)'));end=s.index('    ret = wait_ready();',start)
s=s[:start]+'''    int fd = open("/dev/wmtdetect", O_RDWR | O_CLOEXEC);
    if (fd < 0) return -errno;
    int ret = stage_wifi_record(fd);
    close(fd);
    if (ret) return ret;
    ret = check_regular(FW_DIR "/WIFI_RAM_CODE_8163", 1);
    if (ret) return ret;
    ssize_t n;
'''+s[end:];put(p,s)
p=D/'radio/sepolicy/p00a_radio.te';s=p.read_text();s=s.replace('allow kernel p00a_radio_nvram_file:dir search;\n','').replace('allow kernel p00a_radio_nvram_file:file r_file_perms;\n','');put(p,s)
p=D/'radio/init.p00a-radio.rc';s=p.read_text();start=s.index('on post-fs-data\n');end=s.index('\non property:vendor.p00a.wmt.ready=1 && property:persist.vendor.p00a.bluetooth.enable=1',start);block=s[start:end];s=s[:start]+s[end:];insert=s.index('on post-fs-data &&');s=s[:insert]+block+'\n'+s[insert:];put(p,s)
receipt=R/'evidence/product-staging.json';shutil.copy2(receipt,R/'evidence/product-staging-r3.json');data=json.loads(receipt.read_text())
for p in changes:
 q=Path(p)
 if q.is_relative_to(D):data['changes'][str(q.relative_to(D))]['after']={'sha256':hashlib.sha256(q.read_bytes()).hexdigest()}
data['kernel_calibration_boundary']='Root loader passes a real read-only514-byte file descriptor; kernel validates logical512-byte record, caches once, rejects changes; workers use cached data, not vendor pathname opens.'
receipt.write_text(json.dumps(data,indent=2)+'\n');(R/'evidence/wifi-snapshot-fix.json').write_text(json.dumps({'changes':changes,'calibration_payloads_accessed':False,'new_scalar_ioctl':'_IOW(w,5,int), argument is existing read-only FD','record_container_bytes':514,'logical_snapshot_bytes':512,'no_kernel_nvram_path_grants':True,'no_factory_write_api':True},indent=2)+'\n');(R/'evidence/wifi-snapshot-fix.patch').write_text(''.join(diff))
