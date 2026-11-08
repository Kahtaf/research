from pathlib import Path
import json
R=Path('/srv/android/asus-linux49-power-supply-phase-capture-20261107-431dfb9c')
print((R/'evidence/build-status.json').read_text() if (R/'evidence/build-status.json').exists() else 'not started')
print('\n'.join((R/'evidence/compile-1.log').read_text().splitlines()[-8:]) if (R/'evidence/compile-1.log').exists() else '')
