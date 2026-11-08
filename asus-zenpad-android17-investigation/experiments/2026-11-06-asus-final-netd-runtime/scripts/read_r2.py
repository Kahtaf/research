from pathlib import Path
O=Path('/srv/android/asus-final-netd-runtime-20261106')
print((O/'run-r2-actual/serial.log').read_text(errors='replace')[-11000:])
