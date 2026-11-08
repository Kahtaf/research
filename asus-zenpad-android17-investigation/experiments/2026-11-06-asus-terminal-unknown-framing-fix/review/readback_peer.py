"""Finite owned fake peer for the production parent's two-frame readback reply."""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import struct
import sys
import time

resource.setrlimit(resource.RLIMIT_CPU,(5,5))
signal.alarm(5)
try:resource.setrlimit(resource.RLIMIT_DATA,(128*1024**2,128*1024**2))
except (ValueError,OSError):pass

kind,path=sys.argv[1:]
assert kind=='readback'
config=json.loads(Path(path).read_text())
def readn(n):
    data=b''
    while len(data)<n:
        block=os.read(0,n-len(data))
        if not block:raise EOFError()
        data+=block
    return data
magic,op,n=struct.unpack('<4sII',readn(12))
payload=readn(n)
assert magic==b'RSC1' and op==6 and struct.unpack('<II',payload)==(25,0)
started=time.monotonic()
with open(config['log'],'a') as out:out.write(json.dumps({'target_op':op})+'\n')
data=b'owned fake readback'
def send(op,data):
    os.write(1,b'RSC1'+struct.pack('<II',op,len(data))+data)
    with open(config['log'],'a') as out:out.write(json.dumps({'reply_op':op,'request_elapsed_seconds':time.monotonic()-started})+'\n')
time.sleep(.12)
send(0x86,hashlib.sha256(data).digest())
time.sleep(.12)
send(0x87,data)
assert os.read(0,1)==b''
