"""Read only selected actual JSON fields and their Make serialization."""
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
from integrate import read, sha, need, acquire, native_processes
plan = read(r / 'inputs/plan.json')
lock = acquire(plan)
need(os.fstat(lock.fileno()).st_ino == 15018964 and not native_processes(plan), 'Lock/job mismatch')
a = Path(plan['aosp'])
matches = {}
for p in (a / 'build/make/core').rglob('*.mk'):
    lines = p.read_text().splitlines()
    indices = {j for i, line in enumerate(lines)
               if any(k in line for k in ('ProductNotDebuggableInUserdebug', 'define add_json_bool'))
               for j in range(max(0, i - 4), min(len(lines), i + 9))}
    if indices:
        matches[str(p.relative_to(a))] = {'sha256': sha(p), 'selected_lines': '\n'.join(f'{i+1}: {lines[i]}' for i in sorted(indices))}
config_path = a / 'out/soong/.intermediates/build/soong/product_config/product_config.json'
config = read(config_path)
selected = {k: config.get(k) for k in ('ProductNotDebuggableInUserdebug', 'Debuggable', 'Eng', 'DeviceName')}
generator_input = a / 'out/soong/.intermediates/build/soong/system-build.prop/android_common/build.prop'
intermediate = {'path': str(generator_input), 'sha256': sha(generator_input),
                'properties': [x for x in generator_input.read_text().splitlines() if x.partition('=')[0].strip() in ('ro.secure', 'ro.debuggable', 'ro.adb.secure')]}
print(json.dumps({'serialization_sources': matches, 'actual_product_config': {'path': str(config_path), 'sha256': sha(config_path), 'selected': selected},
                  'actual_system_property_intermediate': intermediate}, indent=2))
