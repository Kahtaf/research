set -eu
python3 - <<'PY'
from pathlib import Path
import ctypes,json,os,signal,subprocess,time
run=Path('/run/asus-alpine')
receipt=json.loads((run/'sd-capsule-update.json').read_text())
assert receipt['status']=='RECOVERY_UPDATED_FULL_READBACK_VERIFIED_NO_REBOOT'
assert not os.path.ismount('/mnt/asus-root-stage')
assert 'asus-alpine-root / tmpfs ' in Path('/proc/mounts').read_text()
p=int((run/'dashboard.pid').read_text())
args=Path('/proc',str(p),'cmdline').read_bytes().split(b'\0')
assert args[:2]==[b'/usr/bin/python3',b'/usr/local/bin/asus-dashboard.py']
os.kill(p,signal.SIGTERM)
for i in range(40):
 if not Path('/proc',str(p)).exists():break
 time.sleep(.1)
else:raise AssertionError('Dashboard still running')
os.sync()
subprocess.run(['mount','-o','remount,ro','/mnt/alpine-sd'],check=True)
entries=[x.split() for x in Path('/proc/mounts').read_text().splitlines() if x.split()[1]=='/mnt/alpine-sd']
assert len(entries)==1 and 'ro' in entries[0][3].split(',')
os.sync()
print('SD_SEALED_READ_ONLY; invoking stock kernel recovery restart, BCB unchanged',flush=True)
libc=ctypes.CDLL(None,use_errno=True)
rc=libc.syscall(ctypes.c_long(142),ctypes.c_ulong(0xfee1dead),ctypes.c_ulong(672274793),ctypes.c_ulong(0xa1b2c3d4),ctypes.c_char_p(b'recovery'))
raise OSError(ctypes.get_errno(),'Recovery restart returned '+str(rc))
PY
