"""Offline finite supervisor. Starts only this spike's unittest and fake peers."""
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
with (ROOT/'evidence/qa.log').open('w') as log:
    proc=subprocess.Popen([sys.executable,'-B',str(ROOT/'tests/test_bounded.py')],
                          stdout=log,stderr=subprocess.STDOUT)
    try:
        code=proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:proc.wait(timeout=1)
        except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=1)
        raise
print((ROOT/'evidence/qa.log').read_text())
sys.exit(code)
