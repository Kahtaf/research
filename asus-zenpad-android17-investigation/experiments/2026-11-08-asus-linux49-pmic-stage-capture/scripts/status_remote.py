from pathlib import Path
R=Path('/srv/android/asus-linux49-pmic-stage-capture-20261108-a1ff82b1')
print((R/'evidence/build-status.json').read_text())
p=R/'evidence/compile-1.log'
if p.exists(): print('\n'.join(p.read_text().splitlines()[-12:]))
