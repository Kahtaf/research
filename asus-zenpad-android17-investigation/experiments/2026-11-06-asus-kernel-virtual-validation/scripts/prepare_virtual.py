#!/usr/bin/env python3
"""Isolate the generic GIC fix from all saved ASUS hardware candidates."""
from pathlib import Path
import json
import subprocess

root = Path('/srv/android/asus-virtual-validation')
original = Path('/srv/android/asus-android17/kernel-network')
source = root / 'kernel'
baseline = 'de61780979adc3c52068e244aa62ae0369c00527'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=original, text=True).strip() == baseline
assert not source.exists()
subprocess.run(['git', 'worktree', 'add', '-b', 'asus-virtual-validation', str(source), baseline], cwd=original, check=True)
path = source / 'drivers/irqchip/irq-gic-v3.c'
text = path.read_text()
old = '#ifndef CONFIG_MTK_SYSIRQ\n\t/* setup polarity registers */'
new = '#if defined(CONFIG_MTK_GIC) && !defined(CONFIG_MTK_SYSIRQ)\n\t/* setup polarity registers */'
assert text.count(old) == 1
path.write_text(text.replace(old, new))
subprocess.run(['git', 'add', 'drivers/irqchip/irq-gic-v3.c'], cwd=source, check=True)
subprocess.run(['git', 'commit', '-m', 'irqchip: gic-v3: limit MediaTek polarity hook to MediaTek GIC'], cwd=source, check=True)
patch = subprocess.check_output(['git', 'format-patch', '-1', '--stdout'], cwd=source)
(root / 'gic-platform-guard.patch').write_bytes(patch)
metadata = {'baseline': baseline,
            'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip(),
            'change': 'Only the platform condition around the existing MediaTek-specific GIC polarity hook',
            'hardware_candidates_modified': False}
(root / 'source-provenance.json').write_text(json.dumps(metadata, indent=2) + '\n')
print(json.dumps(metadata, indent=2))
