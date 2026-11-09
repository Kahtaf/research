set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
python3 - <<'PY'
import json,secrets,subprocess,socket,time
from pathlib import Path
p=Path('/run/asus-goodix/browser-proof.json')
if p.exists():p.unlink()
with Path('/run/asus-goodix/browser-workload-visible.log').open('ab') as out:
 child=subprocess.Popen(['/usr/bin/python3','/tmp/browser-workload.py','--nonce',secrets.token_hex(12),'--output',str(p)],stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
Path('/run/asus-goodix/workload-server.pid').write_text(str(child.pid)+'\n')
for i in range(30):
 assert child.poll() is None,'Workload server exited'
 try:s=socket.create_connection(('127.0.0.1',8081),timeout=.2);s.close();break
 except OSError:time.sleep(.1)
else:raise AssertionError('Workload server not listening')
PY
window=$(head -1 /run/asus-goodix/browser-window-ids.txt)
restore_dashboard() {
 set +e
 xdotool windowactivate --sync "$window"
 xdotool key --clearmodifiers ctrl+l
 xdotool type --clearmodifiers --delay 1 'http://127.0.0.1:8080/'
 xdotool key Return
}
trap restore_dashboard EXIT
xdotool windowactivate --sync "$window"
xdotool key --clearmodifiers ctrl+l
xdotool type --clearmodifiers --delay 1 'http://127.0.0.1:8081/'
xdotool key Return
for n in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
 [ ! -s /run/asus-goodix/browser-proof.json ] || break
 sleep 1
done
python3 - <<'PY'
from pathlib import Path
import json
p=Path('/run/asus-goodix/browser-proof.json');d=json.loads(p.read_text());assert d['passed'] and all(d[k] for k in ('modernJavaScript','fetch','canvas','localStorage','indexedDB')),d
print(json.dumps(d,indent=2));print('VISIBLE_FIREFOX_MODERN_WORKLOAD_PASS')
PY
xwd -root -silent -out /tmp/firefox-modern-visible.xwd
