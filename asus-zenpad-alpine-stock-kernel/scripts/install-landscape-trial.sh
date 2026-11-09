set -eu
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
stage=Path('/tmp/asus-landscape-stage')
run=Path('/run/asus-goodix/rotation-trial')
backup=Path('/mnt/alpine-sd/2026-11-08-asus-alpine/private/desktop-before-landscape')
assert Path('/etc/asus-goodix/native-touch').read_text()=='libinput-v1\n'
assert not Path('/etc/asus-goodix/rotation').exists() and not run.exists() and not backup.exists()
expected={
 '/usr/local/bin/asus-goodix-desktop':'084c4e883dbf97f9552622f54975e60fb69d77f749e34455bb14063798620454',
 '/etc/asus-alpine/start-desktop':'44b03b466eb588a512130c959510e3c5357690664e2286427f5c14948d78cc52',
 '/etc/X11/asus-goodix-libinput.conf':'1201386080f17c415244dd2dd99a96d54f32cff4fb52c4976dd48264a90ef8f4',
}
for name,digest in expected.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,name
manifest=json.loads((stage/'manifest.json').read_text())
for name,digest in manifest.items():assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest,name
for name in ('Ext_Speaker_Amp_Switch','Speaker_Amp_Switch'):
 assert ': values=0' in subprocess.check_output(['amixer','-c','0','cget','name='+name],text=True)
assert Path('/proc/asound/card0/pcm0p/sub0/status').read_text().strip()=='closed'
media=Path('/tmp/asus-media-trial');state=json.loads((media/'state.json').read_text())
if state['status']=='running':
 pid=state['pid'];process=Path('/proc',str(pid),'cmdline')
 assert process.read_bytes().endswith(b'/tmp/asus-media-trial/media-fixture.py\0')
 (media/'STOP').touch()
 for _ in range(50):
  if not Path('/proc',str(pid)).exists():break
  time.sleep(.1)
 else:raise AssertionError('Media fixture did not finish')
backup.mkdir(mode=0o700)
for name in expected:shutil.copy2(name,backup/Path(name).name)
(backup/'sha256.json').write_text(json.dumps(expected)+'\n')
shutil.copy2(media/'state.json',backup/'media-state.json')
shutil.copy2(media/'speaker-result.json',backup/'speaker-result.json')
for source,target in (
 ('asus-goodix-desktop','/usr/local/bin/asus-goodix-desktop'),
 ('goodix-xorg-config.py','/usr/local/bin/goodix-xorg-config.py'),
 ('start-desktop','/etc/asus-alpine/start-desktop'),
):
 target=Path(target);temporary=target.with_name(target.name+'.landscape-new')
 assert not temporary.exists()
 temporary.write_bytes((stage/source).read_bytes());temporary.chmod(0o755);temporary.replace(target)
run.mkdir(mode=0o700)
for source,target in (('rotation-watchdog.py','watchdog.py'),('landscape-fixture.py','fixture.py')):
 shutil.copy2(stage/source,run/target)
print('LANDSCAPE_HELPERS_STAGED; no rotation marker yet; portrait path unchanged')
PY
# Close the real profile before selecting landscape. No new X server on failure.
/bin/sh /tmp/asus-landscape-stage/stop-owned-desktop.sh
python3 - <<'PY'
from pathlib import Path
import json,os,subprocess,time
run=Path('/run/asus-goodix/rotation-trial')
assert not Path('/tmp/.X11-unix/X0').exists()
(run/'REQUEST').write_text('cw-v1\n')
with (run/'watchdog.log').open('wb') as output:
 child=subprocess.Popen(['python3',str(run/'watchdog.py')],stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
for _ in range(40):
 assert child.poll() is None,'Watchdog exited'
 if (run/'state.json').exists():break
 time.sleep(.1)
else:raise AssertionError('Watchdog not armed')
state=json.loads((run/'state.json').read_text());assert state['pid']==child.pid and state['phase']=='ARMED'
assert Path('/proc',str(child.pid),'cmdline').read_bytes().endswith(b'/run/asus-goodix/rotation-trial/watchdog.py\0')
os.sync()
subprocess.run(['/etc/asus-alpine/start-desktop'],check=True,timeout=10)
print('LANDSCAPE_START_WITH_LIVE_REVERT_WATCHDOG',child.pid)
PY
