from pathlib import Path
R=Path('/srv/android/asus-linux49-power-supply-phase-capture-20261107-431dfb9c')
s=(R/'evidence/compile-1.log').read_text().splitlines()
for i,l in enumerate(s):
 if 'error:' in l:print('\n'.join(s[max(0,i-4):i+6]))
