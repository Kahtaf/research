from pathlib import Path
import json
R=Path('/srv/android/asus-linux49-work-dispatch-capture-20261107-b4702f9a')
p=R/'evidence/build-status.json';print(p.read_text() if p.exists() else 'not yet started')
p=R/'evidence/compile-1.log';print('\n'.join(p.read_text().splitlines()[-12:]) if p.exists() else 'no log yet')
