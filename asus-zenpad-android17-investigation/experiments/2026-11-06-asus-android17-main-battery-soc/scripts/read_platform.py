#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parents[1]
ssh=json.loads((R.parent/'2026-11-06-asus-android17-battery-gauge/evidence/remote-source.json').read_text())['ssh']
repos={'hardware/interfaces':'a0221f11248a924532444fc7de85d41998b9fe1e','system/core':'65d661b1a536701e8b118be4e9728d7b5ca727c9','frameworks/base':'696a5773fa284f53429dbb6c3e5dcc96bf5bd0b3'}
files={'hardware/interfaces':['health/aidl/default/HalHealthLoop.cpp','health/aidl/default/Android.bp','health/aidl/default/include/health-impl/HalHealthLoop.h','health/aidl/android/hardware/health/IHealth.aidl'],'system/core':['healthd/include/healthd/healthd.h'],'frameworks/base':['services/core/java/com/android/server/health/HealthServiceWrapperAidl.java','services/core/java/com/android/server/health/HealthRegCallbackAidl.java']}
result=[]
for repo,paths in files.items():
 for p in paths:
  data=subprocess.check_output(ssh+['git -C /srv/android/lineage24/'+repo+' show '+repos[repo]+':'+p]); f=R/'source/platform'/repo/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
  result.append(dict(repository=repo,revision=repos[repo],path=p,sha256=hashlib.sha256(data).hexdigest()))
(R/'evidence/platform-additional-source.json').write_text(json.dumps(result,indent=2)+'\n')
print('Read',len(result),'pinned platform files; no remote writes.')
