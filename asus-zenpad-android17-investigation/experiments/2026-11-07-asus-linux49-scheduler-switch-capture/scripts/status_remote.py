from pathlib import Path
import json
R=Path('/srv/android/asus-linux49-scheduler-switch-capture-20261107-3d26cc95')
p=R/'evidence/build-status.json';print(p.read_text() if p.exists() else 'not yet started')
p=R/'evidence/compile-1.log';print('\n'.join(p.read_text().splitlines()[-12:]) if p.exists() else 'no log yet')
