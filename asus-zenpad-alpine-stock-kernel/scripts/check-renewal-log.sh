set -eu
p=$(cat /run/asus-alpine/udhcpc.pid)
python3 - "$p" <<'PY'
from pathlib import Path
import os,signal,sys
p=int(sys.argv[1]);args=Path('/proc',str(p),'cmdline').read_bytes().split(b'\0')
assert Path(args[0].decode()).name=='udhcpc' and b'wlan0' in args,args
os.kill(p,signal.SIGUSR1)
PY
sleep 3
tail -15 /run/asus-alpine/udhcpc.log
printf 'LEASE_ACK_RECORDS='; grep -c 'lease of' /run/asus-alpine/udhcpc.log
