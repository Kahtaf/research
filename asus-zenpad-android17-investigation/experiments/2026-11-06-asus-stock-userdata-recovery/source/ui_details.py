from pathlib import Path
from elfaudit import ELF
import struct,json
S=Path(__file__).resolve().parents[1];e=ELF(S/'inputs/recovery__sbin_recovery')
print('segments',e.ph)
for a in [0x55e7e0,0x55e880,0x55de00]:
 print('TABLE',hex(a))
 for k in range(0,0xb0,8):
  v=struct.unpack('<Q',e.bytes(a+k,a+k+8))[0]
  try:s=e.string(v)
  except ValueError:s=''
  print(hex(a+k),hex(v),repr(s) if v>=0x51d000 else '')
# show menu strings and pointer locations
for term in [b'Wipe data',b'wipe data',b'Yes --',b'Reboot system',b'Volume',b'volume',b'power button']:
 start=0
 while (p:=e.data.find(term,start))>=0:
  print('STRING',hex(p),repr(e.data[p:p+150].split(b'\0')[0])); start=p+len(term)
for name,a,b in [('main-device',0x4057c0,0x405e00),('menu-dispatch',0x406000,0x4062a0),('volumes',0x40764c,0x407870),('bcb',0x401598,0x401860)]:
 (S/f'evidence/{name}.txt').write_text(e.listing(a,b))
