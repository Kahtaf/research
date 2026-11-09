set -eu
python3 - <<'PY'
from pathlib import Path
import json
folder=Path('/tmp/asus-media-trial')
d=json.loads((folder/'state.json').read_text())
process=Path('/proc',str(d['pid']),'cmdline')
live=process.exists() and process.read_bytes().endswith(b'/tmp/asus-media-trial/media-fixture.py\0')
print('MEDIA_SERVER',json.dumps({'status':d['status'],'pid_live_and_owned':live,'speaker':d.get('speaker')}))
print('LAST_BROWSER_EVENTS')
for e in d['events'][-3:]:print(json.dumps(e))
PY
amixer -c 0 cget name=Ext_Speaker_Amp_Switch
amixer -c 0 cget name=Speaker_Amp_Switch
cat /proc/asound/card0/pcm0p/sub0/status
printf '\nROTATION MARKERS\n'
for file in /etc/asus-goodix/rotation /run/asus-goodix/rotation-trial/REQUEST; do
 if [ -e "$file" ]; then echo "$file"; cat "$file"; else echo "$file absent"; fi
done
