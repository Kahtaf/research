set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
python3 /etc/asus-alpine/validate-wmt-loader.py /run/asus-alpine/wmt-loader.trace
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess,time,urllib.request
for i in range(100):
 r=subprocess.run(['xinput','list','--long'],capture_output=True,text=True)
 if 'XITouchClass' in r.stdout and 'Max number of touches: 16' in r.stdout:break
 time.sleep(.1)
else:raise AssertionError('Native touch class absent after reboot')
assert 'Touch mode: direct' in r.stdout
Path('/run/asus-goodix/native-after-boot-xinput.txt').write_text(r.stdout)
assert Path('/etc/asus-goodix/native-touch').read_text()=='libinput-v1\n'
assert '"/dev/input/event' in Path('/run/asus-goodix/native-xorg.conf').read_text()
for i in range(100):
 p=Path('/run/asus-goodix/onboard.pid')
 if p.exists():
  pid=p.read_text().strip();a=Path('/proc',pid,'cmdline').read_bytes().split(b'\0')
  if b'/usr/bin/onboard' in a:break
 time.sleep(.1)
else:raise AssertionError('Automatic keyboard did not start')
owner=int(Path('/root/.mozilla/asus-appliance/lock').readlink().name.rsplit('+',1)[1])
assert b'MOZ_USE_XINPUT2=1' in Path('/proc',str(owner),'environ').read_bytes().split(b'\0')
for p in Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try:a=(p/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,ProcessLookupError):continue
 assert not(a and a[0].endswith(b'/z380m-touchbridge')),'Pointer bridge unexpectedly running'
assert hashlib.sha256(Path('/usr/bin/jwm').read_bytes()).hexdigest()=='107bd16aaaa575750c44b2d3f6cd9606c6759acef3e7464c06e909e793dcd58b'
assert hashlib.sha256(Path('/usr/local/bin/asus-jwm').read_bytes()).hexdigest()=='789dbb085e8485ff69b177cd8da8c4effe75028dfcdbf1cd4119a0959c910bc6'
d=json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3));assert d['requests_saved']>=30
print(json.dumps({'native_direct_touch_contacts':16,'runtime_input_metadata_regenerated':True,'automatic_keyboard_started':True,'firefox_xi2_enabled':True,'pointer_bridge_disabled':True,'packaged_jwm_preserved':True,'dashboard_saved_requests':d['requests_saved']}))
PY
wpa_cli -iwlan0 status | grep '^wpa_state=COMPLETED$'
curl --fail --silent --show-error --max-time 15 https://alpinelinux.org/ --output /dev/null
echo NATIVE_UI_REBOOT_HTTPS_PASS
