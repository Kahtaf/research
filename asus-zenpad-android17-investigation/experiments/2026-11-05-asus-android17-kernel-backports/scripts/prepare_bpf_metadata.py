#!/usr/bin/env python3
"""Port real program tags and ARM64 JIT lengths before object-info support."""
from pathlib import Path
import hashlib
import json
import subprocess

root = Path('/srv/android/asus-virtual-validation')
base = root / 'kernel-fd'
source = root / 'kernel-meta'
reference = Path('/srv/android/reference-kernel')
expected = 'fcb1b6c2de6348e2724981dcd520dec631ed5255'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=base, text=True).strip() == expected
assert not source.exists()
subprocess.run(['git', 'worktree', 'add', '-b', 'asus-bpf-metadata', str(source), expected], cwd=base, check=True)

def replace(text, old, new):
    assert text.count(old) == 1, old[:100]
    return text.replace(old, new)

def function(text, signature):
    start = text.index(signature)
    opening = text.index('{', start)
    depth = 0
    for i in range(opening, len(text)):
        depth += (text[i] == '{') - (text[i] == '}')
        if depth == 0:
            return text[start:i + 1]
    raise ValueError(signature)

donor_commit = '5ae1915fde1a778be406151efdd0ad81eb9a5968'
donor_core = subprocess.check_output(['git', 'show', donor_commit + ':kernel/bpf/core.c'], cwd=reference, text=True)
tag = function(donor_core, 'int bpf_prog_calc_tag(')
assert 'vmalloc(raw_size)' in tag and 'vfree(raw)' in tag
p = source / 'kernel/bpf/core.c'
p.write_text(replace(p.read_text(), 'static bool bpf_is_jmp_and_has_target', tag + '\n\nstatic bool bpf_is_jmp_and_has_target'))
p = source / 'include/linux/bpf.h'
p.write_text(replace(p.read_text(), 'bool bpf_prog_array_compatible(struct bpf_array *array, const struct bpf_prog *fp);',
                     'bool bpf_prog_array_compatible(struct bpf_array *array, const struct bpf_prog *fp);\nint bpf_prog_calc_tag(struct bpf_prog *fp);'))
p = source / 'include/linux/filter.h'
text = p.read_text()
text = replace(text, '#include <linux/capability.h>', '#include <linux/capability.h>\n#include <linux/cryptohash.h>')
text = replace(text, '#define MAX_BPF_STACK\t512', '#define MAX_BPF_STACK\t512\n#define BPF_TAG_SIZE 8')
text = replace(text, '\tu32\t\t\tlen;\t\t/* Number of filter blocks */', '\tu32\t\t\tlen;\t\t/* Number of filter blocks */\n\tu32 jited_len;\n\tu8 tag[BPF_TAG_SIZE];')
anchor = 'static inline unsigned int bpf_prog_size('
helpers = '''static inline u32 bpf_prog_insn_size(const struct bpf_prog *prog)
{
\treturn prog->len * sizeof(struct bpf_insn);
}

static inline u32 bpf_prog_tag_scratch_size(const struct bpf_prog *prog)
{
\treturn round_up(bpf_prog_insn_size(prog) + sizeof(__be64) + 1,
\t\t\tSHA_MESSAGE_BYTES);
}

'''
text = replace(text, anchor, helpers + anchor)
p.write_text(text)
p = source / 'kernel/bpf/verifier.c'
text = p.read_text()
start = text.index('static int replace_map_fd_with_map_ptr(')
end = text.index('\n}', start)
part = text[start:end]
part = replace(part, '\tint i, j, err;\n', '\tint i, j, err;\n\n\terr = bpf_prog_calc_tag(env->prog);\n\tif (err)\n\t\treturn err;\n')
text = text[:start] + part + text[end:]
text = replace(text, '\tif ((*prog)->len <= 0 || (*prog)->len > BPF_MAXINSNS)\n\t\treturn -E2BIG;\n\n', '')
p.write_text(text)
p = source / 'kernel/bpf/syscall.c'
text = p.read_text()
text = replace(text, '\tif (attr->insn_cnt >= BPF_MAXINSNS)\n\t\treturn -EINVAL;', '\tif (attr->insn_cnt == 0 || attr->insn_cnt > BPF_MAXINSNS)\n\t\treturn -E2BIG;')
fdinfo = '''#ifdef CONFIG_PROC_FS
static void bpf_prog_show_fdinfo(struct seq_file *m, struct file *filp)
{
\tconst struct bpf_prog *prog = filp->private_data;
\tchar tag[sizeof(prog->tag) * 2 + 1] = {};

\tbin2hex(tag, prog->tag, sizeof(prog->tag));
\tseq_printf(m, "prog_type:\\t%u\\nprog_jited:\\t%u\\nprog_tag:\\t%s\\njited_len:\\t%u\\nmemlock:\\t%llu\\n",
\t\t   prog->type, prog->jited, tag, prog->jited_len,
\t\t   prog->pages * 1ULL << PAGE_SHIFT);
}
#endif

'''
text = replace(text, 'const struct file_operations bpf_prog_fops = {', fdinfo + 'const struct file_operations bpf_prog_fops = {\n#ifdef CONFIG_PROC_FS\n\t.show_fdinfo = bpf_prog_show_fdinfo,\n#endif')
p.write_text(text)
p = source / 'arch/arm64/net/bpf_jit_comp.c'
p.write_text(replace(p.read_text(), '\tprog->jited = 1;', '\tprog->jited = 1;\n\tprog->jited_len = image_size;'))
# Add the corresponding stable netlink tag attributes and dumps, adapting the
# original digest patch's final naming without importing its obsolete digest.
patch = Path('/srv/android/asus-android17/patches/bpf-info-prerequisites/0001-5199702654ff.patch')
paths = ['include/uapi/linux/pkt_cls.h', 'include/uapi/linux/tc_act/tc_bpf.h',
         'net/sched/act_bpf.c', 'net/sched/cls_bpf.c']
includes = ['--include=' + name for name in paths]
subprocess.run(['git', 'apply', '--check', *includes, str(patch)], cwd=source, check=True)
subprocess.run(['git', 'apply', *includes, str(patch)], cwd=source, check=True)
for name in paths:
    p = source / name
    p.write_text(p.read_text().replace('DIGEST', 'TAG').replace('->digest', '->tag'))
subprocess.run(['git', 'diff', '--check'], cwd=source, check=True)
subprocess.run(['git', 'add', 'include', 'kernel/bpf', 'arch/arm64/net/bpf_jit_comp.c', 'net/sched'], cwd=source, check=True)
subprocess.run(['git', 'commit', '-m', 'bpf: port stable tags, boundary handling and ARM64 JIT length'], cwd=source, check=True)
out = root / 'meta'
out.mkdir()
metadata = {'baseline': expected, 'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip(),
            'tag_function_reference': donor_commit, 'tag_function_sha256': hashlib.sha256(tag.encode()).hexdigest(),
            'scope': 'Tag calculation/fdinfo/netlink, instruction-count boundary and ARM64 JIT length; object-info syscall not yet added',
            'hardware_candidates_modified': False}
(out / 'source-provenance.json').write_text(json.dumps(metadata, indent=2) + '\n')
(out / 'bpf-meta.patch').write_bytes(subprocess.check_output(['git', 'format-patch', '-1', '--stdout'], cwd=source))
print(json.dumps(metadata, indent=2))
