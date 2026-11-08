from pathlib import Path
import json
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');lines=(R/'run-runtime/serial.log').read_text(errors='replace').splitlines();print('\n'.join(f'{i+1}: {l}' for i,l in enumerate(lines) if 1885<=i<=2005));print('LAST',lines[-1]);print((R/'evidence/runtime-resume.log').read_text(errors='replace')[-2500:])
