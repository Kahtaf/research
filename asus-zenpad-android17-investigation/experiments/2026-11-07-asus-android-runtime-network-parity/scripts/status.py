from pathlib import Path
import datetime
R=Path('/srv/android/asus-android-runtime-network-parity-20261107');E=R/'evidence'
print(datetime.datetime.now(datetime.timezone.utc).isoformat())
for n in ['integration.json','build-started.json','build-result.json']:
 p=E/n
 if p.exists():print(n,p.read_text())
for n in ['build.log','build-runner.log']:
 p=E/n
 if p.exists():
  with p.open('rb') as f:f.seek(max(0,p.stat().st_size-1800));print(n,p.stat().st_size,f.read().decode(errors='replace'))
