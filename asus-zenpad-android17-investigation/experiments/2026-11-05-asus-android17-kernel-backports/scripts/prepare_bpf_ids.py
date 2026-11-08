#!/usr/bin/env python3
"""Adapt the first BPF ID feature group in a new, virtual-test-only worktree.

Based on pinned donor commits d46c559eaa9a, d5f3d0c41ff3 and 073754cb9d24.
Their original hunks depend on newer trace/kallsyms and map-allocation code that
this MT8163 baseline does not have. Keep its existing lifetimes; allocate map IDs
after successful memlock charging, and unwind IDs before releasing storage.
No device access or hardware candidate mutation occurs here.
"""
from pathlib import Path
import json
import subprocess

root = Path('/srv/android/asus-virtual-validation')
original = root / 'kernel'
source = root / 'kernel-ids'
baseline = 'be15c78f96d53b5bf2e3a2db0ed272be803518fd'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=original, text=True).strip() == baseline
assert not source.exists()
subprocess.run(['git', 'worktree', 'add', '-b', 'asus-bpf-ids', str(source), baseline], cwd=original, check=True)

def replace(text, old, new):
    assert text.count(old) == 1, old[:100]
    return text.replace(old, new)

path = source / 'include/linux/bpf.h'
text = path.read_text()
text = replace(text, '\tu32 map_flags;\n', '\tu32 map_flags;\n\tu32 id;\n')
text = replace(text, '\tu32 max_ctx_offset;\n', '\tu32 max_ctx_offset;\n\tu32 id;\n')
path.write_text(text)
path = source / 'include/uapi/linux/bpf.h'
text = path.read_text()
text = replace(text, '\tBPF_PROG_DETACH,\n', '''\tBPF_PROG_DETACH,
\t/* Keep the upstream command numbers. TEST_RUN is not implemented here. */
\tBPF_PROG_TEST_RUN = 10,
\tBPF_PROG_GET_NEXT_ID = 11,
\tBPF_MAP_GET_NEXT_ID = 12,
''')
text = replace(text, '} __attribute__((aligned(8)));', '''\tstruct { /* BPF_*_GET_NEXT_ID */
\t\t__u32 start_id;
\t\t__u32 next_id;
\t};
} __attribute__((aligned(8)));''')
path.write_text(text)
path = source / 'kernel/bpf/syscall.c'
text = path.read_text()
text = replace(text, '#include <linux/version.h>\n', '#include <linux/version.h>\n#include <linux/kernel.h>\n#include <linux/idr.h>\n')
text = replace(text, 'DEFINE_PER_CPU(int, bpf_prog_active);\n', '''DEFINE_PER_CPU(int, bpf_prog_active);
static DEFINE_IDR(prog_idr);
static DEFINE_SPINLOCK(prog_idr_lock);
static DEFINE_IDR(map_idr);
static DEFINE_SPINLOCK(map_idr_lock);
''')
for kind, expression in [('map', 'map->id'), ('prog', 'prog->aux->id')]:
    anchor = '/* called from workqueue */' if kind == 'map' else 'static void __bpf_prog_put_rcu'
    functions = f'''static int bpf_{kind}_alloc_id(struct bpf_{kind} *{kind})
{{
\tint id;

\tspin_lock_bh(&{kind}_idr_lock);
\tid = idr_alloc_cyclic(&{kind}_idr, {kind}, 1, INT_MAX, GFP_ATOMIC);
\tif (id > 0)
\t\t{expression} = id;
\tspin_unlock_bh(&{kind}_idr_lock);
\tif (WARN_ON_ONCE(!id))
\t\treturn -ENOSPC;
\treturn id > 0 ? 0 : id;
}}

static void bpf_{kind}_free_id(struct bpf_{kind} *{kind})
{{
\tif (!{expression})
\t\treturn;
\tspin_lock_bh(&{kind}_idr_lock);
\tidr_remove(&{kind}_idr, {expression});
\tspin_unlock_bh(&{kind}_idr_lock);
}}

'''
    text = replace(text, anchor, functions + anchor)
text = replace(text, '''\tif (atomic_dec_and_test(&map->refcnt)) {
\t\tINIT_WORK''', '''\tif (atomic_dec_and_test(&map->refcnt)) {
\t\tbpf_map_free_id(map);
\t\tINIT_WORK''')
text = replace(text, '''\tif (atomic_dec_and_test(&prog->aux->refcnt))
\t\tcall_rcu(&prog->aux->rcu, __bpf_prog_put_rcu);''', '''\tif (atomic_dec_and_test(&prog->aux->refcnt)) {
\t\tbpf_prog_free_id(prog);
\t\tcall_rcu(&prog->aux->rcu, __bpf_prog_put_rcu);
\t}''')
text = replace(text, '''\terr = bpf_map_new_fd(map, f_flags);
\tif (err < 0)
\t\t/* failed to allocate fd */
\t\tgoto free_map;

\treturn err;

free_map:''', '''\terr = bpf_map_alloc_id(map);
\tif (err)
\t\tgoto free_map;

\terr = bpf_map_new_fd(map, f_flags);
\tif (err < 0)
\t\tgoto free_id;

\treturn err;

free_id:
\tbpf_map_free_id(map);
free_map:''')
text = replace(text, '''\terr = bpf_prog_new_fd(prog);
\tif (err < 0)
\t\t/* failed to allocate fd */
\t\tgoto free_used_maps;

\treturn err;

free_used_maps:''', '''\terr = bpf_prog_alloc_id(prog);
\tif (err)
\t\tgoto free_used_maps;

\terr = bpf_prog_new_fd(prog);
\tif (err < 0)
\t\tgoto free_id;

\treturn err;

free_id:
\tbpf_prog_free_id(prog);
free_used_maps:''')
anchor = 'SYSCALL_DEFINE3(bpf, int, cmd, union bpf_attr __user *, uattr, unsigned int, size)'
function = '''#define BPF_OBJ_GET_NEXT_ID_LAST_FIELD next_id

static int bpf_obj_get_next_id(const union bpf_attr *attr,
\t\t\t      union bpf_attr __user *uattr,
\t\t\t      struct idr *idr, spinlock_t *lock)
{
\tint next_id, err = 0;

\tif (CHECK_ATTR(BPF_OBJ_GET_NEXT_ID) || attr->start_id >= INT_MAX)
\t\treturn -EINVAL;
\tif (!capable(CAP_SYS_ADMIN))
\t\treturn -EPERM;

\tnext_id = attr->start_id + 1;
\tspin_lock_bh(lock);
\tif (!idr_get_next(idr, &next_id))
\t\terr = -ENOENT;
\tspin_unlock_bh(lock);
\tif (!err)
\t\terr = put_user(next_id, &uattr->next_id);
\treturn err;
}

'''
text = replace(text, anchor, function + anchor)
anchor = '\tswitch (cmd) {\n'
text = replace(text, anchor, anchor + '''\tcase BPF_PROG_GET_NEXT_ID:
\t\terr = bpf_obj_get_next_id(&attr, uattr, &prog_idr, &prog_idr_lock);
\t\tbreak;
\tcase BPF_MAP_GET_NEXT_ID:
\t\terr = bpf_obj_get_next_id(&attr, uattr, &map_idr, &map_idr_lock);
\t\tbreak;
''')
path.write_text(text)
subprocess.run(['git', 'diff', '--check'], cwd=source, check=True)
subprocess.run(['git', 'add', 'include/linux/bpf.h', 'include/uapi/linux/bpf.h', 'kernel/bpf/syscall.c'], cwd=source, check=True)
subprocess.run(['git', 'commit', '-m', 'bpf: adapt program/map IDs and enumeration to the MT8163 baseline'], cwd=source, check=True)
test = root / 'ids'
test.mkdir()
metadata = {'baseline': baseline,
            'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip(),
            'change': 'Adapt program/map IDs and GET_NEXT_ID; preserve upstream numeric ABI and permission checks',
            'upstream_donor_commits': ['d46c559eaa9aeff8d1b470fabf5a48fa5bb488a2', 'd5f3d0c41ff3f57d5c3961976bcb4b3b25ff59c7', '073754cb9d245f85db9c952f4b84334395e19d34'],
            'hardware_candidates_modified': False}
(test / 'source-provenance.json').write_text(json.dumps(metadata, indent=2) + '\n')
(test / 'bpf-ids.patch').write_bytes(subprocess.check_output(['git', 'format-patch', '-1', '--stdout'], cwd=source))
print(json.dumps(metadata, indent=2))
