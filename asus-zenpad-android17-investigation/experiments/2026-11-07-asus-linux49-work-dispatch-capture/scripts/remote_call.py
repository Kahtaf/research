from pathlib import Path
import os, subprocess, sys
from vm import R, channel
script=Path(sys.argv[1]).resolve().read_bytes()
os.chdir(R)
p=subprocess.run(channel()+['python3 -B -'],input=script,capture_output=True)
if p.returncode:sys.stderr.buffer.write(p.stderr);sys.stdout.buffer.write(p.stdout);raise SystemExit(p.returncode)
sys.stdout.buffer.write(p.stdout)
