set -eu
printf 'MEDIA RESULT\n'
python3 - <<'PY'
import json
from pathlib import Path
d=json.loads(Path('/tmp/asus-media-trial/state.json').read_text())
for e in d['events']:
 if e['event'] in ('loaded','error','play-rejected','ten-second-result','ready'):print(json.dumps(e))
PY
printf '\nBROWSER MEDIA ERRORS\n'
tail -80 /run/asus-goodix/browser.log
printf '\nEFFECTIVE AUDIO CONFIG\n'
zcat /proc/config.gz | sed -n '/CONFIG_MTK_SPEAKER/p;/CONFIG_OF[= ]/p;/CONFIG_MTK_LEGACY/p;/CONFIG_SND_SOC_MT/p;/CONFIG_SND_SOC_MTK/p'
printf '\nCODEC DT\n'
python3 - <<'PY'
from pathlib import Path
import struct
for base in (Path('/proc/device-tree'),Path('/sys/firmware/devicetree/base')):
 if not base.is_dir():continue
 for compatible in base.rglob('compatible'):
  value=compatible.read_bytes()
  if b'mediatek,mt8163-soc-codec-63xx' in value:
   print(str(compatible),repr(value))
   prop=compatible.parent/'extspkamp-gpio'
   raw=prop.read_bytes(); cells=struct.unpack('>'+'I'*(len(raw)//4),raw)
   print('extspkamp-gpio',cells)
   for phandle in base.rglob('phandle'):
    if phandle.read_bytes()==raw[:4]:
     print('GPIO CONTROLLER',phandle.parent)
     cp=phandle.parent/'compatible'
     if cp.exists():print(repr(cp.read_bytes()))
 break
PY
printf '\nPCM STATUS\n'
cat /proc/asound/card0/pcm0p/sub0/status /proc/asound/card0/pcm0p/sub0/hw_params
