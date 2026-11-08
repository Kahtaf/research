from pathlib import Path
p=Path(__file__).resolve().parents[1]/'stagedpatches/kernel-input/drivers/misc/mediatek/connectivity/common/conn_soc/linux/pri/wmt_dev.c'
s=p.read_text().replace('P_WMT_PATCH_INFO pPatchInfo = NULL;', 'P_WMT_PATCH_INFO pPatchInfo = NULL;\nstatic UINT32 p00a_patch_mask;')
s=s.replace('kfree(pPatchInfo);\n\tpPatchInfo = NULL;', 'kfree(pPatchInfo);\n\tpPatchInfo = NULL;\n\tgDevWmt.pWmtPatchInfo = NULL;\n\tgDevWmt.patchNum = 0;\n\tp00a_patch_mask = 0;')
s=s.replace('cmdLen = osal_strlen(pCmd) < NAME_MAX ? osal_strlen(pCmd) : NAME_MAX;', 'cmdLen = min_t(size_t, count, min_t(size_t, osal_strlen(pCmd), NAME_MAX));')
a=s.index('\tcase WMT_IOCTL_SET_PATCH_NUM:{');b=s.index('\n\tcase WMT_IOCTL_WMT_COREDUMP_CTRL:',a)
s=s[:a]+'''	case WMT_IOCTL_SET_PATCH_NUM:
		if (!arg || arg > MAX_PATCH_NUM)
			return -EINVAL;
		wmt_dev_patch_info_free();
		pAtchNum = arg;
		pPatchInfo = kcalloc(pAtchNum, sizeof(WMT_PATCH_INFO), GFP_KERNEL);
		if (!pPatchInfo)
			return -ENOMEM;
		/* Publish count/pointer together only after all unique entries arrive. */
		break;
	case WMT_IOCTL_SET_PATCH_INFO: {
		WMT_PATCH_INFO patch;
		UINT32 seq;
		if (!pPatchInfo)
			return -EINVAL;
		if (copy_from_user(&patch, (void __user *)arg, sizeof(patch)))
			return -EFAULT;
		seq = patch.dowloadSeq;
		if (!seq || seq > pAtchNum || (p00a_patch_mask & BIT(seq - 1)) ||
		    patch.patchName[0] != '/' ||
		    !memchr(patch.patchName, 0, sizeof(patch.patchName)))
			return -EINVAL;
		pPatchInfo[seq - 1] = patch;
		p00a_patch_mask |= BIT(seq - 1);
		if (p00a_patch_mask == BIT(pAtchNum) - 1) {
			wmt_lib_set_patch_num(pAtchNum);
			wmt_lib_set_patch_info(pPatchInfo);
		}
		break;
	}
'''+s[b:]
# Invalid unknown ioctls are errors, not success.
p.write_text(s)
