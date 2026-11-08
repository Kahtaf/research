"""Local fixture child only. No sockets, ADB, device nodes or external commands."""
import json
import os
from pathlib import Path
import struct
import sys
import time

config = Path(sys.argv[1])
c = json.loads(config.read_text())
a = sys.argv[2:]
with (config.parent/'calls.jsonl').open('a') as out:
    out.write(json.dumps({'argv':a,'pid':os.getpid()})+'\n')
mode=c.get('mode','ok')
if a[-2:]==['devices','-l']:
    rows='DEVICE_SERIAL_REDACTED device usb:1-3.2 product:p00a_target_rescue model:P00A_target_rescue device:p00a transport_id:17\n'
    if mode=='wrong_usb': rows=rows.replace('DEVICE_SERIAL_REDACTED','different')
    if mode=='stale_usb':
        calls=(config.parent/'calls.jsonl').read_text().count('devices')
        if calls>1: rows=rows.replace('transport_id:17','transport_id:18')
    os.write(1,('List of devices attached\n'+rows+'\n').encode())
    sys.exit(0)
if a[-1:] == ['features']:
    os.write(1,b'cmd,shell_v2\n' if mode!='no_v2' else b'cmd\n')
    sys.exit(0)
assert a==['direct'] or a[-5:]==['shell','-T','-e','none','rescue-v1'],a
if mode=='backpressure':
    time.sleep(10)
    sys.exit(0)
request=bytearray()
while len(request)<80:
    part=os.read(0,min(3,80-len(request)))
    if not part:sys.exit(3)
    request.extend(part)
(config.parent/'request.bin').write_bytes(request)
if mode=='stall':time.sleep(10)
if mode=='eof':sys.exit(0)
reply=b'RSC1'+struct.pack('<II',0x82,48)+b'EPHEMERAL_TEST_TOKEN_NEVER_LOGGED!'[:32]+bytes([1])*16
assert len(reply)==60,len(reply)
if mode=='bad_header':reply=b'bad!'+reply[4:]
if mode=='bad_bitmap':reply=reply[:-1]+b'\x00'
if mode=='stderr':
    block=b'EPHEMERAL_TEST_TOKEN_NEVER_LOGGED!'*256
    for _ in range(160):os.write(2,block)
for byte in reply:
    os.write(1,bytes([byte]))
    if mode=='slow':time.sleep(.02)
    elif mode=='fragment':time.sleep(.001)
extra=os.read(0,1)
(config.parent/'host-eof.json').write_text(json.dumps({'eof':not extra,'extra':extra.hex()}))
if mode=='trailer':os.write(1,b'bad')
if mode=='hang_exit':time.sleep(10)
sys.exit(19 if mode=='remote_nonzero' else 0)
