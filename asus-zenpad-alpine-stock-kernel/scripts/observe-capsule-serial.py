#!/usr/bin/env python3
"""Read only the newly enumerated, identity-matched Alpine USB serial device."""
from pathlib import Path
import glob,json,os,plistlib,select,subprocess,termios,time
HERE=Path(__file__).resolve().parents[1]
DEST=HERE/'private/live'
baseline=set(json.loads((DEST/'serial-baseline.json').read_text()))
def matched(node):
 if isinstance(node,list):return any(matched(x) for x in node)
 if not isinstance(node,dict):return False
 if node.get('idVendor')==0x0e8d and node.get('idProduct')==0x2007 and node.get('USB Product Name') in ('ASUS-Alpine-RAM','ASUS_Alpine_RAM') and str(node.get('USB Serial Number','')).strip()=='asus-alpine-ram':return True
 return matched(node.get('IORegistryEntryChildren',[]))
start=time.monotonic();port=None
while time.monotonic()-start<120:
 new=set(glob.glob('/dev/cu.usbmodem*'))-baseline
 if new:
  raw=subprocess.check_output(['ioreg','-p','IOUSB','-l','-a'],timeout=8)
  if matched(plistlib.loads(raw)):
   assert len(new)==1,'Ambiguous new serial ports'
   port=new.pop();(DEST/'usb-capsule.plist').write_bytes(raw);break
 time.sleep(2)
if port is None:
 (DEST/'capsule-serial-state.json').write_text(json.dumps({'state':'NO_MATCHED_SERIAL_WITHIN_120_SECONDS'})+'\n')
 print('NO_MATCHED_SERIAL_WITHIN_120_SECONDS',flush=True);raise SystemExit(2)
print('IDENTITY_MATCHED_CAPSULE_SERIAL',port,flush=True)
fd=os.open(port,os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
attrs=termios.tcgetattr(fd);attrs[0]=0;attrs[1]=0;attrs[2]=termios.CS8|termios.CREAD|termios.CLOCAL;attrs[3]=0;attrs[4]=termios.B115200;attrs[5]=termios.B115200;attrs[6][termios.VMIN]=0;attrs[6][termios.VTIME]=0;termios.tcsetattr(fd,termios.TCSANOW,attrs)
raw=bytearray();sent=False;deadline=time.monotonic()+120
with (DEST/'capsule-serial.log').open('wb') as log:
 while time.monotonic()<deadline:
  ready,_,_=select.select([fd],[],[],1)
  if not ready:continue
  try:chunk=os.read(fd,65536)
  except BlockingIOError:continue
  except OSError:break
  if not chunk:continue
  raw.extend(chunk);log.write(chunk);log.flush()
  if not sent and (b'ASUS Alpine RAM root' in raw or b'RESCUE:' in raw):
   command=b"\necho CAPSULE_READ_ONLY_AUDIT_BEGIN; cat /etc/asus-alpine-ram-release; uname -rm; cat /proc/1/comm; ip -o -4 addr show wlan0; cat /run/asus-alpine/sysinit.log; tail -30 /run/asus-alpine/wmt-launcher.log; cat /run/asus-alpine/wmt-loader.trace; echo CAPSULE_READ_ONLY_AUDIT_END\n"
   os.write(fd,command);sent=True
  if sent and raw.count(b'CAPSULE_READ_ONLY_AUDIT_END')>=2:break
os.close(fd)
state={'state':'READ_ONLY_AUDIT_CAPTURED' if sent else 'SERIAL_PRESENT_NO_EXPECTED_BANNER','port':port,'bytes':len(raw)}
(DEST/'capsule-serial-state.json').write_text(json.dumps(state)+'\n')
print(json.dumps(state),flush=True)
