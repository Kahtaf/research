#!/usr/bin/env python3
"""Adapt BPF lookup-by-ID and reference lifetimes in a separate virtual branch."""
from pathlib import Path
import json
import subprocess

root = Path('/srv/android/asus-virtual-validation')
base = root / 'kernel-ids'
source = root / 'kernel-fd'
expected = '34a8afba47785b0ff9dc2a72dade73c945a54a55'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=base, text=True).strip() == expected
assert not source.exists()
subprocess.run(['git', 'worktree', 'add', '-b', 'asus-bpf-fdlookup', str(source), expected], cwd=base, check=True)

def replace(text, old, new):
    assert text.count(old) == 1, old[:140]
    return text.replace(old, new)

p = source / 'include/uapi/linux/bpf.h'
text = p.read_text()
text = replace(text, '\tBPF_MAP_GET_NEXT_ID = 12,', '\tBPF_MAP_GET_NEXT_ID = 12,\n\tBPF_PROG_GET_FD_BY_ID = 13,\n\tBPF_MAP_GET_FD_BY_ID = 14,')
text = replace(text, '\t\t__u32 start_id;\n', '\t\tunion {\n\t\t\t__u32 start_id;\n\t\t\t__u32 prog_id;\n\t\t\t__u32 map_id;\n\t\t};\n')
p.write_text(text)
p = source / 'kernel/bpf/syscall.c'
text = p.read_text()
for kind, field in [('map', 'map->id'), ('prog', 'prog->aux->id')]:
    old = f'''static void bpf_{kind}_free_id(struct bpf_{kind} *{kind})
{{
\tif (!{field})
\t\treturn;
\tspin_lock_bh(&{kind}_idr_lock);
\tidr_remove(&{kind}_idr, {field});
\tspin_unlock_bh(&{kind}_idr_lock);
}}'''
    new = f'''static void bpf_{kind}_free_id(struct bpf_{kind} *{kind}, bool do_idr_lock)
{{
\tif (!{field})
\t\treturn;
\tif (do_idr_lock)
\t\tspin_lock_bh(&{kind}_idr_lock);
\telse
\t\t__acquire(&{kind}_idr_lock);
\tidr_remove(&{kind}_idr, {field});
\tif (do_idr_lock)
\t\tspin_unlock_bh(&{kind}_idr_lock);
\telse
\t\t__release(&{kind}_idr_lock);
}}'''
    text = replace(text, old, new)
    text = replace(text, f'void bpf_{kind}_put(struct bpf_{kind} *{kind})\n',
                   f'static void __bpf_{kind}_put(struct bpf_{kind} *{kind}, bool do_idr_lock)\n')
    text = replace(text, f'\t\tbpf_{kind}_free_id({kind});\n', f'\t\tbpf_{kind}_free_id({kind}, do_idr_lock);\n')
    anchor = 'void bpf_map_put_with_uref' if kind == 'map' else 'EXPORT_SYMBOL_GPL(bpf_prog_put);'
    wrapper = f'''void bpf_{kind}_put(struct bpf_{kind} *{kind})
{{
\t__bpf_{kind}_put({kind}, true);
}}

'''
    text = replace(text, anchor, wrapper + anchor)
    suffix = ', bool uref' if kind == 'map' else ''
    extra = '\tif (uref)\n\t\tatomic_inc(&map->usercnt);\n' if kind == 'map' else ''
    count = 'map->refcnt' if kind == 'map' else 'prog->aux->refcnt'
    helper = f'''/* Caller holds {kind}_idr_lock, so zero-ref objects cannot disappear. */
static struct bpf_{kind} *bpf_{kind}_inc_not_zero(struct bpf_{kind} *{kind}{suffix})
{{
\tint refold = __atomic_add_unless(&{count}, 1, 0);

\tif (refold >= BPF_MAX_REFCNT) {{
\t\t__bpf_{kind}_put({kind}, false);
\t\treturn ERR_PTR(-EBUSY);
\t}}
\tif (!refold)
\t\treturn ERR_PTR(-ENOENT);
{extra}\treturn {kind};
}}

'''
    anchor = '/* helper to convert user pointers' if kind == 'map' else 'static struct bpf_prog *__bpf_prog_get'
    text = replace(text, anchor, helper + anchor)
    flags = ', f_flags' if kind == 'map' else ''
    put = 'bpf_map_put_with_uref(map)' if kind == 'map' else 'bpf_prog_put(prog)'
    label = 'free_map' if kind == 'map' else 'free_used_maps'
    old = f'''\terr = bpf_{kind}_new_fd({kind}{flags});
\tif (err < 0)
\t\tgoto free_id;

\treturn err;

free_id:
\tbpf_{kind}_free_id({kind});
{label}:'''
    new = f'''\terr = bpf_{kind}_new_fd({kind}{flags});
\tif (err < 0) {{
\t\t/* An ID lookup may already own another live reference. */
\t\t{put};
\t\treturn err;
\t}}

\treturn err;

{label}:'''
    text = replace(text, old, new)
    argument = ', true' if kind == 'map' else ''
    flags = ', O_RDWR' if kind == 'map' else ''
    command = f'BPF_{kind.upper()}_GET_FD_BY_ID'
    function = f'''#define {command}_LAST_FIELD {kind}_id

static int bpf_{kind}_get_fd_by_id(const union bpf_attr *attr)
{{
\tstruct bpf_{kind} *{kind};
\tu32 id = attr->{kind}_id;
\tint fd;

\tif (CHECK_ATTR({command}))
\t\treturn -EINVAL;
\tif (!capable(CAP_SYS_ADMIN))
\t\treturn -EPERM;
\tif (id >= INT_MAX)
\t\treturn -ENOENT;
\tspin_lock_bh(&{kind}_idr_lock);
\t{kind} = idr_find(&{kind}_idr, id);
\tif ({kind})
\t\t{kind} = bpf_{kind}_inc_not_zero({kind}{argument});
\telse
\t\t{kind} = ERR_PTR(-ENOENT);
\tspin_unlock_bh(&{kind}_idr_lock);
\tif (IS_ERR({kind}))
\t\treturn PTR_ERR({kind});
\tfd = bpf_{kind}_new_fd({kind}{flags});
\tif (fd < 0)
\t\t{put};
\treturn fd;
}}

'''
    text = replace(text, 'SYSCALL_DEFINE3(bpf, int, cmd, union bpf_attr __user *, uattr, unsigned int, size)',
                   function + 'SYSCALL_DEFINE3(bpf, int, cmd, union bpf_attr __user *, uattr, unsigned int, size)')
    text = replace(text, '\tswitch (cmd) {\n', f'\tswitch (cmd) {{\n\tcase {command}:\n\t\terr = bpf_{kind}_get_fd_by_id(&attr);\n\t\tbreak;\n')
p.write_text(text)
subprocess.run(['git', 'diff', '--check'], cwd=source, check=True)
subprocess.run(['git', 'add', 'include/uapi/linux/bpf.h', 'kernel/bpf/syscall.c'], cwd=source, check=True)
subprocess.run(['git', 'commit', '-m', 'bpf: add ID lookup with reference-safe creation failure cleanup'], cwd=source, check=True)
out = root / 'fd'
out.mkdir()
metadata = {'baseline': expected,
            'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip(),
            'donor_commits': ['413af41f256d04d1db11ae96968761da3184c313', '4656edb079ccf6e8aab4ca8f44567c1767d891d5', 'c8a7a85ebbb1e374357249b37236efcc14cf5554', '73ccf8d23efdac4ca90ea3be4ac471273fda5617'],
            'adaptations': ['Existing two-argument map FD constructor, default read/write flags',
                            'Drop map user references on both creator and lookup FD failures',
                            'Reject out-of-range IDs before older IDR lookup'],
            'hardware_candidates_modified': False}
(out / 'source-provenance.json').write_text(json.dumps(metadata, indent=2) + '\n')
(out / 'bpf-fd.patch').write_bytes(subprocess.check_output(['git', 'format-patch', '-1', '--stdout'], cwd=source))
print(json.dumps(metadata, indent=2))
