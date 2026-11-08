from pathlib import Path
O=Path('/srv/android/asus-final-bpf-runtime-20261106')
for R in sorted(O.glob('run-*')):
 print(R.name)
 if (R/'serial.log').exists():print((R/'serial.log').read_text(errors='replace')[-16000:])
