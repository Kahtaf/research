#!/usr/bin/env python3
"""Read pinned platform files, without changing remote source or build state."""
import json,subprocess,hashlib
from pathlib import Path
r=Path(__file__).resolve().parents[1]
ssh=json.loads((r/'evidence/remote-source.json').read_text())['ssh']
files=[('hardware/interfaces','a0221f11248a924532444fc7de85d41998b9fe1e','health/aidl/default/Health.cpp'),('hardware/interfaces','a0221f11248a924532444fc7de85d41998b9fe1e','health/aidl/default/include/health-impl/Health.h'),('system/core','65d661b1a536701e8b118be4e9728d7b5ca727c9','healthd/BatteryMonitor.cpp'),('frameworks/base','696a5773fa284f53429dbb6c3e5dcc96bf5bd0b3','services/core/java/com/android/server/BatteryService.java')]
result=[]
for repo,rev,path in files:
    data=subprocess.check_output(ssh+['git -C /srv/android/lineage24/'+repo+' show '+rev+':'+path])
    out=r/'evidence/platform'/repo/path;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
    result.append({'repository':repo,'revision':rev,'path':path,'sha256':hashlib.sha256(data).hexdigest()})
(r/'evidence/platform-source.json').write_text(json.dumps(result,indent=2)+'\n')
print('Read four pinned Health/platform files. No remote writes.')
