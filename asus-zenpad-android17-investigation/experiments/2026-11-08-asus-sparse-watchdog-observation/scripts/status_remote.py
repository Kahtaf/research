from pathlib import Path
import json
R=Path('/srv/android/asus-sparse-watchdog-observation-20261108-e0b1a1ba')
print((R/'evidence/build-status.json').read_text())
p=R/'evidence/compile-1.log'
print('\n'.join(p.read_text(errors='replace').splitlines()[-8:]))
