set -eu
[ ! -e /run/asus-alpine/udhcpc.pid ]
timeout -k 2 20 udhcpc -n -t 3 -T 4 -p /run/asus-alpine/udhcpc.pid -i wlan0 -s /etc/asus-alpine/udhcpc </dev/null > /run/asus-alpine/udhcpc.log 2>&1
p=$(cat /run/asus-alpine/udhcpc.pid)
python3 - "$p" <<'PY'
from pathlib import Path
import os,signal,sys
pid=int(sys.argv[1]);args=Path('/proc',str(pid),'cmdline').read_bytes().split(b'\0')
assert any(b'udhcpc' in a for a in args) and b'wlan0' in args,args
os.kill(pid,signal.SIGUSR1)
PY
sleep 2
kill -0 "$p"
tail -12 /run/asus-alpine/udhcpc.log
curl -fsS --max-time 8 https://alpinelinux.org/ -o /tmp/dhcp-renewal-https.html
wc -c /tmp/dhcp-renewal-https.html
echo RESIDENT_DHCP_RENEWAL_AND_TLS_PASS
