"""Read current selected property producers; never run the build system."""
from pathlib import Path
import json
import os
import resource
import signal
import subprocess
import sys
import re

resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
signal.alarm(1190)
root = Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
sys.path.insert(0, str(root / 'scripts'))
from integrate import read, sha, need, acquire, native_processes
plan = read(root / 'inputs/plan.json')
lock = acquire(plan)
need(os.fstat(lock.fileno()).st_ino == 15018964, 'Wrong original lock')
need(not native_processes(plan), 'Active native job')
a = Path(plan['aosp'])
selected = ['build/make/tools/buildinfo.sh', 'build/make/core/sysprop.mk',
            'build/soong/scripts/gen_build_prop.py', 'device/asus/p00a', 'vendor/lineage/config']
matches = []
pattern = re.compile(r'ro\.debuggable|PRODUCT_NOT_DEBUGGABLE_IN_USERDEBUG|TARGET_BUILD_VARIANT')
for rel in selected:
    base = a / rel
    candidates = base.rglob('*') if base.is_dir() else [base]
    for p in candidates:
        if p.is_file() and not p.is_symlink() and p.suffix in ('.mk', '.sh', '.py', '.prop', '.bp'):
            for line_number, line in enumerate(p.read_text().splitlines(), 1):
                if pattern.search(line):
                    matches.append(f'{p}:{line_number}:{line}')
sources = {}
for rel in selected[:3]:
    p = a / rel
    if p.is_file():
        sources[rel] = {'sha256': sha(p), 'content': p.read_text()}
product = Path(plan['product_out'])
properties = {}
for rel in ['system/build.prop', 'system/etc/prop.default', 'root/prop.default',
            'system/system_ext/etc/build.prop', 'system/product/etc/build.prop', 'system/vendor/build.prop']:
    p = product / rel
    if p.is_file():
        lines = p.read_text().splitlines()
        chosen = [f'{i + 1}: {line}' for i, line in enumerate(lines)
                  if line.partition('=')[0].strip() in ('ro.secure', 'ro.debuggable', 'ro.adb.secure')]
        properties[rel] = {'sha256': sha(p), 'security_property_lines': chosen}
tools = Path(plan['staging']) / 'full-boot-tools/scripts'
packager = tools / 'package_full_boot.py'
print(json.dumps({'lock_inode': os.fstat(lock.fileno()).st_ino, 'native_jobs_at_entry': [],
                  'selected_search': '\n'.join(matches), 'generator_sources': sources,
                  'installed_properties': properties,
                  'packager': {'path': str(packager), 'sha256': sha(packager), 'content': packager.read_text()},
                  'out_top_level_ninja_files': [str(p) for p in (a / 'out').glob('*ninja*')],
                  'soong_top_level_ninja_files': [str(p) for p in (a / 'out/soong').glob('*ninja*')]}, indent=2))
