from pathlib import Path
import json,subprocess
R=Path('/srv/android/asus-linux49-retained-clock-capture-20261107-fef31ed4')
d=json.loads((R/'evidence/build-status.json').read_text())
print(json.dumps(d,indent=2));print('\n'.join((R/'evidence/compile-1.log').read_text(errors='replace').splitlines()[-12:]))
