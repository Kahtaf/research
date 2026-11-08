from pathlib import Path
R=Path('/srv/android/asus-sparse-observer-liveness-20261108-e6799dac')
print((R/'evidence/build-status.json').read_text())
p=R/'evidence/compile-1.log'
if p.exists(): print('\n'.join(p.read_text().splitlines()[-12:]))
