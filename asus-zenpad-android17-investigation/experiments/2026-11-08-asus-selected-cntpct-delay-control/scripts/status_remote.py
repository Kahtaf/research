from pathlib import Path
import json
R=Path('/srv/android/asus-selected-cntpct-delay-control-20261108-2ac3b1e4')
print((R/'evidence/build-status.json').read_text())
p=R/'evidence/compile-1.log'
if p.exists():print('\n'.join(p.read_text().splitlines()[-8:]))
