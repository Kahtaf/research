"""Use legacy ADB shell framing, retaining a nonce-bound remote exit status."""
import hashlib
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys

REAL='/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools/adb'
assert hashlib.sha256(Path(REAL).read_bytes()).hexdigest()=='1811e253b21b12cbfda7201ebaf86c10e7ddcb5c606a7a81f7c82b4c429c2d3b'
args=sys.argv[1:]
if len(args)<3 or args[:3]!=['-s','DEVICE_SERIAL_REDACTED','shell']:
    os.execv(REAL,[REAL,*args])
command=args[3:]
while command and command[0] in ('-T','-x'):
    command=command[1:]
if not command:
    raise SystemExit('Interactive shell is not supported by this adapter')
token='ASUS_LEGACY_'+secrets.token_hex(24)
body='(\n'+' '.join(command)+'\n)\nasus_legacy_status=$?\nprintf "\\n'+token+'=%s\\n" "$asus_legacy_status"\nexit 0\n'
result=subprocess.run([REAL,*args[:2],'shell','-T','-x',body],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
sys.stderr.buffer.write(result.stderr)
if result.returncode:
    sys.stdout.buffer.write(result.stdout)
    raise SystemExit(result.returncode)
pattern=rb'\n'+token.encode()+rb'=(\d{1,3})\r?\n$'
matches=list(re.finditer(pattern,result.stdout))
if len(matches)!=1 or not 0<=int(matches[0][1])<=255:
    sys.stdout.buffer.write(result.stdout)
    sys.stderr.write('Missing complete remote command status; do not retry automatically\n')
    raise SystemExit(254)
sys.stdout.buffer.write(result.stdout[:matches[0].start()])
raise SystemExit(int(matches[0][1]))
