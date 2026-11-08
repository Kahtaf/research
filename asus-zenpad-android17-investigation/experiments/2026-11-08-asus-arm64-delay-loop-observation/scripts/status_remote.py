from pathlib import Path
R=Path('/srv/android/asus-arm64-delay-loop-observation-20261108-f3da846c')
print((R/'evidence/build-status.json').read_text())
p=R/'evidence/compile-1.log'
if p.exists(): print('\n'.join(p.read_text().splitlines()[-12:]))
