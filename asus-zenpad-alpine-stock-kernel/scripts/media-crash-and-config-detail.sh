set -eu
printf 'KERNEL CONFIG FORMAT\n'
if [ -r /proc/config.gz ]; then
 ls -l /proc/config.gz
 zcat /proc/config.gz | head -12
printf '\nAUDIO CONFIG FLAGS\n'
zcat /proc/config.gz | sed -n '/SPEAKER/p;/LEGACY/p;/CONFIG_OF/p;/SND_SOC/p' | head -65
else
 echo EFFECTIVE_CONFIG_NOT_EXPOSED
fi
printf '\nPENDING CRASH REASONS\n'
python3 - <<'PY'
from pathlib import Path
import json
roots=[Path('/root/.mozilla/firefox/Crash Reports/pending'),Path('/root/.mozilla/asus-appliance/minidumps')]
for root in roots:
 if not root.is_dir():continue
 for p in root.glob('*.extra'):
  try:d=json.loads(p.read_text())
  except (OSError,ValueError):continue
  print(p.name)
  for k in ('MozCrashReason','CrashReason','CrashType','ProcessType','UtilityActorsName','OOMAllocationSize','StackTraces'):
   if k in d:print(k,str(d[k])[:4000])
PY
printf '\nPLAYBACK PCM CAPABILITIES (no stream opened)\n'
aplay -l
