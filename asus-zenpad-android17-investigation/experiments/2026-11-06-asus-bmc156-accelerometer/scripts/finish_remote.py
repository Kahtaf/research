from pathlib import Path
import subprocess,sys
R=Path('/srv/android/asus-bmc156-accelerometer-r1')
p=subprocess.run(['python3',str(R/'scripts/verify_final.py')],capture_output=True,text=True)
(R/'evidence/final-preservation.stdout').write_text(p.stdout+p.stderr)
if p.returncode:print(p.stdout+p.stderr,file=sys.stderr);raise SystemExit(p.returncode)
p=subprocess.run(['python3',str(R/'scripts/export_remote.py')],capture_output=True,text=True)
if p.returncode:print(p.stderr,file=sys.stderr);raise SystemExit(p.returncode)
print(p.stdout,end='')
