from pathlib import Path
import difflib,hashlib,json
R=Path('/srv/android/asus-network-runtime');K=R/'kernel';out=R/'staged-map-info';out.mkdir(exist_ok=True)
changes={}
f='include/uapi/linux/bpf.h';old=(K/f).read_text();new=old.replace('\tBPF_MAP_GET_FD_BY_ID = 14,','\tBPF_MAP_GET_FD_BY_ID = 14,\n\tBPF_OBJ_GET_INFO_BY_FD = 15,');new=new.replace('union bpf_attr {','/* Initial upstream map-info ABI. Program info is not implemented here. */\nstruct bpf_map_info {\n\t__u32 type;\n\t__u32 id;\n\t__u32 key_size;\n\t__u32 value_size;\n\t__u32 max_entries;\n\t__u32 map_flags;\n} __attribute__((aligned(8)));\n\nunion bpf_attr {');new=new.replace('} __attribute__((aligned(8)));\n\n/* integer', '\tstruct { /* BPF_OBJ_GET_INFO_BY_FD */\n\t\t__u32 bpf_fd;\n\t\t__u32 info_len;\n\t\t__aligned_u64 info;\n\t} info;\n} __attribute__((aligned(8)));\n\n/* integer');assert new!=old;changes[f]=(old,new)
f='kernel/bpf/syscall.c';old=(K/f).read_text();addition='''/*
 * Map metadata follows the initial upstream BPF_OBJ_GET_INFO_BY_FD ABI.
 * A held file reference protects the map and its immutable attributes from
 * concurrent close/unpin. Possession of a map fd authorizes metadata access;
 * the syscall's existing unprivileged-BPF and LSM checks still apply.
 *
 * Program metadata needs separate tag/instruction-dump backports. Report it
 * as unsupported rather than returning incomplete or invented program data.
 */
#define BPF_OBJ_GET_INFO_BY_FD_LAST_FIELD info.info

static int bpf_map_get_info_by_fd(struct bpf_map *map,
                                 const union bpf_attr *attr,
                                 union bpf_attr __user *uattr)
{
	struct bpf_map_info __user *uinfo = u64_to_ptr(attr->info.info);
	struct bpf_map_info info = {};
	u32 info_len = attr->info.info_len;
	u32 i;
	unsigned char val;

	if (info_len > PAGE_SIZE)
		return -E2BIG;
	for (i = sizeof(info); i < info_len; i++) {
		if (get_user(val, (unsigned char __user *)uinfo + i))
			return -EFAULT;
		if (val)
			return -E2BIG;
	}
	info_len = min_t(u32, sizeof(info), info_len);
	info.type = map->map_type;
	info.id = map->id;
	info.key_size = map->key_size;
	info.value_size = map->value_size;
	info.max_entries = map->max_entries;
	info.map_flags = map->map_flags;
	if (copy_to_user(uinfo, &info, info_len) ||
	    put_user(info_len, &uattr->info.info_len))
		return -EFAULT;
	return 0;
}

static int bpf_obj_get_info_by_fd(const union bpf_attr *attr,
                                union bpf_attr __user *uattr)
{
	struct fd f;
	int err;

	if (CHECK_ATTR(BPF_OBJ_GET_INFO_BY_FD))
		return -EINVAL;
	f = fdget(attr->info.bpf_fd);
	if (!f.file)
		return -EBADFD;
	if (f.file->f_op == &bpf_map_fops)
		err = bpf_map_get_info_by_fd(f.file->private_data, attr, uattr);
	else if (f.file->f_op == &bpf_prog_fops)
		err = -EOPNOTSUPP;
	else
		err = -EINVAL;
	fdput(f);
	return err;
}

'''
assert 'u64_to_ptr' in old
new=old.replace('SYSCALL_DEFINE3(bpf,',addition+'SYSCALL_DEFINE3(bpf,').replace('\tswitch (cmd) {','\tswitch (cmd) {\n\tcase BPF_OBJ_GET_INFO_BY_FD:\n\t\terr = bpf_obj_get_info_by_fd(&attr, uattr);\n\t\tbreak;');assert new!=old;changes[f]=(old,new)
patch=''
for f,(old,new) in changes.items():
 p=out/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(new)
 patch+=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+f,tofile='b/'+f))
(R/'patches/01-map-info.patch').write_text(patch)
(R/'evidence/map-info-stage.json').write_text(json.dumps({'scope':'Real map metadata only; program info returns EOPNOTSUPP','reference':'a668db21f3cfddc5b73f081c6bb532b1b3351b36:kernel/bpf/syscall.c:bpf_map_get_info_by_fd and fd dispatch','patch_sha256':hashlib.sha256(patch.encode()).hexdigest(),'baseline':{f:hashlib.sha256(old.encode()).hexdigest() for f,(old,new) in changes.items()}},indent=2)+'\n')
print(patch)
