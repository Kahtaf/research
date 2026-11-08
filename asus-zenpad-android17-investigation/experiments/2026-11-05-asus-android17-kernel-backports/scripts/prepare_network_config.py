#!/usr/bin/env python3
"""Create an isolated kernel candidate for the first networking config changes."""
from pathlib import Path
import json
import shutil
import subprocess

root = Path('/srv/android/asus-android17')
source = root / 'kernel'
candidate = root / 'kernel-network'
baseline = '5ab69989839edfa650ed28876f2128e6ed467b9d'

def git(*args, cwd=source):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()

assert git('rev-parse', 'HEAD') == baseline
assert not git('status', '--porcelain'), 'Baseline must remain clean'
assert not candidate.exists(), 'Do not overwrite a previous experiment'
assert not (root / 'build-network').exists(), 'Do not overwrite previous build output'
subprocess.run(['git', 'worktree', 'add', '-b', 'asus-network-bringup', str(candidate), baseline], cwd=source, check=True)
config = candidate / 'arch/arm64/configs/asus_p00a_defconfig'
features = ['BPF_JIT', 'NET_CLS_BPF', 'NET_CLS_MATCHALL', 'NET_ACT_BPF']
for feature in features:
    subprocess.run([str(candidate / 'scripts/config'), '--file', str(config), '-e', feature], check=True)
subprocess.run(['git', 'add', 'arch/arm64/configs/asus_p00a_defconfig'], cwd=candidate, check=True)
subprocess.run(['git', 'commit', '-m', 'arm64: asus: enable existing BPF JIT and traffic control support'], cwd=candidate, check=True)
patch = subprocess.check_output(['git', 'format-patch', '-1', '--stdout'], cwd=candidate)
(root / 'patches/network-0001-enable-existing-support.patch').write_bytes(patch)
build = root / 'build-network'
build.mkdir()
# Preserve every option from the already-built EROFS/hardware candidate.
shutil.copy2(root / 'build-erofs/.config', build / '.config')
for feature in features:
    subprocess.run([str(candidate / 'scripts/config'), '--file', str(build / '.config'), '-e', feature], check=True)
report = {'baseline': baseline, 'candidate': git('rev-parse', 'HEAD', cwd=candidate),
          'enabled_existing_options': features, 'new_kernel_api_backports': [],
          'runtime_validated': False, 'charging_policy': 'unchanged; inhibited in diagnostic DT'}
(root / 'logs/network-config-prepared.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
