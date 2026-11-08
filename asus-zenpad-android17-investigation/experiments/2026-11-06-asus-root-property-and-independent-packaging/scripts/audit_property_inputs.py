"""Trace only the selected property flag and existing producer graph, read-only."""
from pathlib import Path
import json
import os
import resource
import signal
import sys

resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
signal.alarm(1190)
root = Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
sys.path.insert(0, str(root / 'scripts'))
from integrate import read, sha, need, acquire, native_processes
plan = read(root / 'inputs/plan.json')
lock = acquire(plan)
need(os.fstat(lock.fileno()).st_ino == 15018964 and not native_processes(plan), 'Lock/job mismatch')
a = Path(plan['aosp'])
selected = ['device/asus/p00a/lineage_p00a.mk', 'vendor/lineage/config/common.mk',
            'build/make/core/soong_config.mk', 'build/make/core/soong_json.mk']
sources = {}
for rel in selected:
    p = a / rel
    if not p.is_file():
        continue
    lines = p.read_text().splitlines()
    needles = ('ProductNotDebuggableInUserdebug', 'PRODUCT_NOT_DEBUGGABLE_IN_USERDEBUG', 'define add_json_bool')
    indices = {j for i, line in enumerate(lines) if any(n in line for n in needles)
               for j in range(max(0, i - 7), min(len(lines), i + 10))}
    content = p.read_text() if rel == selected[0] else '\n'.join(f'{i + 1}: {lines[i]}' for i in sorted(indices))
    sources[rel] = {'sha256': sha(p), 'selected_content': content}
configs = {}
for rel in ['out/soong/soong.variables', 'out/soong/soong.lineage_p00a.variables']:
    p = a / rel
    if p.is_file():
        config = read(p)
        configs[rel] = {'sha256': sha(p), 'selected': {k: config.get(k) for k in
                       ('ProductNotDebuggableInUserdebug', 'BuildVariant', 'Debuggable', 'Eng', 'DeviceName')}}
graph = []
files = [a / 'out/build-lineage_p00a.ninja', *sorted((a / 'out/soong').glob('build.lineage_p00a*.ninja'))]
for p in files:
    with p.open() as f:
        for number, line in enumerate(f, 1):
            if ('gen_build_prop' in line or 'system_build_prop' in line) and len(line) < 50000:
                graph.append({'file': str(p), 'line': number, 'text': line.rstrip()})
need(len(graph) < 180, 'Unexpectedly broad property graph selection')
print(json.dumps({'sources': sources, 'soong_configs': configs, 'selected_graph': graph}, indent=2))
