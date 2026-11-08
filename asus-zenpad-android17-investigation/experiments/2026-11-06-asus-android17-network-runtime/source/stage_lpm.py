from pathlib import Path
import difflib,json,hashlib
R=Path('/srv/android/asus-network-runtime');K=R/'kernel';out=R/'staged-lpm';out.mkdir(exist_ok=True);changes={}
f='kernel/bpf/lpm_trie.c';new=(R/'inputs/donor'/f).read_text();new=new.replace('#include <uapi/linux/btf.h>','#include <linux/init.h>\n#include <linux/rcupdate.h>')
new=new.replace('trie->map.numa_node','NUMA_NO_NODE').replace('if (!bpf_capable())','if (!capable(CAP_SYS_ADMIN))')
start=new.index('#define LPM_CREATE_FLAG_MASK');end=new.index('\n\n',start);new=new[:start]+'#define LPM_CREATE_FLAG_MASK (BPF_F_NO_PREALLOC | BPF_F_RDONLY | BPF_F_WRONLY)'+new[end:]
new=new.replace('\t    !bpf_map_flags_access_ok(attr->map_flags) ||\n','')
new=new.replace('bpf_map_init_from_attr(&trie->map, attr);','trie->map.map_type = attr->map_type;\n\ttrie->map.key_size = attr->key_size;\n\ttrie->map.value_size = attr->value_size;\n\ttrie->map.max_entries = attr->max_entries;\n\ttrie->map.map_flags = attr->map_flags;')
new=new.replace('attr->value_size + trie->data_size;', 'attr->value_size + trie->data_size;\n\t/* Include the possible intermediate branch node for each real entry. */\n\tcost_per_node += sizeof(struct lpm_trie_node) + trie->data_size;')
new=new.replace('\t/* Always start at the root', '\t/* The 4.9 generic map free path does not wait for program readers. */\n\tsynchronize_rcu();\n\n\t/* Always start at the root')
start=new.index('static int trie_check_btf');new=new[:start]+'''static const struct bpf_map_ops trie_map_ops = {
	.map_alloc = trie_alloc,
	.map_free = trie_free,
	.map_get_next_key = trie_get_next_key,
	.map_lookup_elem = trie_lookup_elem,
	.map_update_elem = trie_update_elem,
	.map_delete_elem = trie_delete_elem,
};

static struct bpf_map_type_list trie_type __read_mostly = {
	.ops = &trie_map_ops,
	.type = BPF_MAP_TYPE_LPM_TRIE,
};

static int __init register_trie_map(void)
{
	bpf_register_map_type(&trie_type);
	return 0;
}
late_initcall(register_trie_map);
'''
# Resolve existence/capacity before allocating, allowing replacement at capacity.
start=new.index('\t/* Allocate and fill a new node */');end=new.index('\t/* Now find a slot',start);alloc=new[start:end];new=new[:start]+new[end:]
alloc=alloc.replace('\tif (trie->n_entries == trie->map.max_entries) {','\tif (!exists && trie->n_entries == trie->map.max_entries) {')
pos=new.index('\t/* If the slot is empty');prefix='''	exists = node && node->prefixlen == key->prefixlen &&
		 matchlen == key->prefixlen && !(node->flags & LPM_TREE_NODE_FLAG_IM);
	if ((exists && flags == BPF_NOEXIST) || (!exists && flags == BPF_EXIST)) {
		ret = exists ? -EEXIST : -ENOENT;
		goto out;
	}

'''
new=new[:pos]+prefix+alloc+new[pos:];start=new.index('static int trie_update_elem');pos=new.index('\tint ret = 0;',start);new=new[:pos]+new[pos:].replace('\tint ret = 0;','\tint ret = 0;\n\tbool exists;',1)
changes[f]=('',new)
f='include/uapi/linux/bpf.h';old=(K/f).read_text();new=old.replace('\tBPF_MAP_TYPE_CGROUP_ARRAY,','\tBPF_MAP_TYPE_CGROUP_ARRAY,\n\t/* 9 and 10 are upstream LRU map types, not implemented here. */\n\tBPF_MAP_TYPE_LPM_TRIE = 11,');new=new.replace('/* Initial upstream map-info ABI.', 'struct bpf_lpm_trie_key {\n\t__u32 prefixlen;\n\t__u8 data[0];\n};\n\n/* Initial upstream map-info ABI.');changes[f]=(old,new)
f='kernel/bpf/Makefile';old=(K/f).read_text();new=old.replace('hashtab.o arraymap.o percpu_freelist.o','hashtab.o arraymap.o percpu_freelist.o lpm_trie.o');changes[f]=(old,new)
patch=''
for f,(old,new) in changes.items():
 p=out/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(new);patch+=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+f if old else '/dev/null',tofile='b/'+f))
(R/'patches/02-lpm-trie.patch').write_text(patch)
(R/'evidence/lpm-stage.json').write_text(json.dumps(dict(donor='a668db21f3cfddc5b73f081c6bb532b1b3351b36',donor_sha256=hashlib.sha256((R/'inputs/donor/kernel/bpf/lpm_trie.c').read_bytes()).hexdigest(),adaptations=['4.9 map registry, attributes, CAP_SYS_ADMIN and no NUMA/BTF/batch APIs','RCU grace period in map_free, absent from old generic map-free workqueue','memlock upper bound includes intermediate nodes','existing-key replacement at full capacity; existence checked before allocation']),indent=2)+'\n')
print('staged',len(patch),'bytes')
