"""Read producer, kernel directory handling and product inheritance semantics."""
from pathlib import Path
import json
import os
import resource
import signal
import sys

resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
signal.alarm(1190)
r = Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
sys.path.insert(0, str(r / 'scripts'))
from integrate import read, sha
plan = read(r / 'inputs/plan.json')
a = Path(plan['aosp'])
files = [a / 'system/core/cpio/mkbootfs.cpp', Path(plan['kernel']) / 'init/initramfs.c',
         a / 'build/make/core/node_fns.mk', a / 'build/make/core/product.mk']
out = {}
for p in files:
    if not p.is_file():
        continue
    lines = p.read_text().splitlines()
    if p.name == 'mkbootfs.cpp':
        needles = ('"dev"', 'S_IFDIR', 'argv[', 'emit_file')
    elif p.name == 'initramfs.c':
        needles = ('case S_IFDIR', 'do_name(', 'sys_mkdir', 'clean_path(')
    elif p.name == 'node_fns.mk':
        needles = ('inherit', '_expand-inherited-values', 'strip $(', 'filter-out')
    else:
        needles = ('PRODUCT_NOT_DEBUGGABLE', 'define inherit-product', 'INHERIT_TAG')
    indices = {j for i, line in enumerate(lines) if any(n in line for n in needles)
               for j in range(max(0, i - 5), min(len(lines), i + 12))}
    out[str(p)] = {'sha256': sha(p), 'selected_lines': '\n'.join(f'{i+1}: {lines[i]}' for i in sorted(indices))}
print(json.dumps(out, indent=2))
