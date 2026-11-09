set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
cat /run/asus-alpine/root-mode
python3 - <<'PY'
from pathlib import Path
import fcntl,json,struct
entries=[p for p in Path('/sys/class/input').glob('event*') if (p/'device/name').read_text().strip()=='goodix-touchscreen']
assert len(entries)==1
p=entries[0];dev=Path('/dev/input',p.name)
with dev.open('rb',buffering=0) as f:
 result={'device':str(dev)}
 for name,request,size,bits in [('abs',0x80404523,64,{'ABS_X':0,'ABS_Y':1,'MT_SLOT':47,'MT_X':53,'MT_Y':54,'MT_TRACKING_ID':57}),('keys',0x80804521,128,{'BTN_TOUCH':330,'BTN_TOOL_FINGER':325}),('properties',0x80084509,8,{'DIRECT':1,'POINTER':0})]:
  buf=bytearray(size);fcntl.ioctl(f.fileno(),request,buf)
  result[name]={k:bool(buf[v//8]&(1<<(v%8))) for k,v in bits.items()}
 print(json.dumps(result))
PY
xinput list --long
apk info -e xf86-input-evdev xf86-input-libinput xf86-video-dummy libxi libxtst
xrandr --query
grep -n 'EVIOCGRAB' /usr/local/src/z380m-touchbridge.c 2>/dev/null || true
