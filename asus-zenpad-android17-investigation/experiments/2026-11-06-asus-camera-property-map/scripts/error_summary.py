from pathlib import Path
import json
r=Path('/srv/android/asus-camera-property-map-20261106');f=Path('/srv/android/asus-camera-arm32-route/cpp-out/sdk37')
for p in f.glob('system/logging/liblog/*/log/log.h'):print('FROZEN LOG',p)
for n in ['commands.json','host-commands.json']:
 d=json.loads((r/n).read_text())
 for c in d:
  print(n,'RC',c['rc']);print('\n'.join(l for l in c['stderr'].splitlines() if 'error:' in l)[:6000])
