set -eu
python3 - <<'PY'
from pathlib import Path
import os,signal,time
profile=Path('/root/.mozilla/asus-appliance')
pid=int((profile/'lock').readlink().name.rsplit('+',1)[1])
args=Path('/proc',str(pid),'cmdline').read_bytes().split(b'\0')
assert args[0]==b'/usr/lib/firefox-esr/firefox-esr' and b'/root/.mozilla/asus-appliance' in args
controller=int(Path('/run/asus-goodix/desktop.pid').read_text())
args=Path('/proc',str(controller),'cmdline').read_bytes().split(b'\0')
assert any(b'asus-goodix-desktop' in a for a in args)
os.kill(pid,signal.SIGTERM)
for i in range(100):
 p=Path('/proc',str(pid))
 if not p.exists() or '\nState:\tZ' in (p/'status').read_text():break
 time.sleep(.1)
else:raise AssertionError('Owned Firefox did not stop after TERM; no forced reboot')
os.kill(controller,signal.SIGTERM)
time.sleep(1)
os.sync()
print('OWNED_FIREFOX_STOPPED_AFTER_WINDOW_CLOSE_AND_TERM; no profile files deleted')
PY
