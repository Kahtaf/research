set -eu
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,stat,subprocess,time
run=Path('/run/asus-goodix/rotation-trial')
assert not (run/'REQUEST').exists() and not (run/'state.json').exists()
assert not Path('/etc/asus-goodix/rotation').exists()
for p in Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try:a=(p/'cmdline').read_bytes().split(b'\0')
 except FileNotFoundError:continue
 if a:
  assert Path(a[0].decode(errors='replace')).name not in ('Xorg','asus-goodix-desktop'),a
assert '/tmp/.X11-unix/X0' not in Path('/proc/net/unix').read_text()
lock=Path('/tmp/.X0-lock');pid=int(lock.read_text().strip())
assert not Path('/proc',str(pid)).exists(),'Display lock PID still exists'
socket=Path('/tmp/.X11-unix/X0');assert stat.S_ISSOCK(socket.lstat().st_mode) and socket.lstat().st_uid==0
lock.unlink();socket.unlink()
pidfile=Path('/run/asus-goodix/desktop.pid')
if pidfile.exists():
 assert not Path('/proc',pidfile.read_text().strip()).exists()
 pidfile.unlink()
candidate=Path('/tmp/asus-landscape-stage/asus-goodix-desktop')
assert hashlib.sha256(candidate.read_bytes()).hexdigest()==json.loads(Path('/tmp/asus-landscape-stage/desktop-revision.json').read_text())['sha256']
target=Path('/usr/local/bin/asus-goodix-desktop');temporary=target.with_name(target.name+'.landscape-new')
assert not temporary.exists();temporary.write_bytes(candidate.read_bytes());temporary.chmod(0o755);temporary.replace(target)
(run/'REQUEST').write_text('cw-v1\n')
with (run/'watchdog.log').open('wb') as output:
 child=subprocess.Popen(['python3',str(run/'watchdog.py')],stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
for _ in range(40):
 assert child.poll() is None
 if (run/'state.json').exists():break
 time.sleep(.1)
else:raise AssertionError('Watchdog not armed')
d=json.loads((run/'state.json').read_text());assert d['pid']==child.pid and d['phase']=='ARMED'
assert Path('/proc',str(child.pid),'cmdline').read_bytes().endswith(b'/run/asus-goodix/rotation-trial/watchdog.py\0')
os.sync();subprocess.run(['/etc/asus-alpine/start-desktop'],check=True,timeout=10)
print('LANDSCAPE_STARTED; verified stale display artifacts removed, watchdog live',child.pid)
PY
