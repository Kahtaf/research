from pathlib import Path
import remote,json
s=r'''
from pathlib import Path
import json,re
P=Path('/srv/android/asus-reviewed-build-kit/r8/attempt/native-evidence/host_init_verifier');R=Path('/srv/android/asus-reviewed-build-kit/r9');rows=[]
p=P/'siso_metrics.json'
for line in p.read_text().splitlines():
 if line.strip():rows.append(json.loads(line))
selected=[r for r in rows if any(s in json.dumps(r) for s in ['system/bpf/loader/bpfloader/','system/vold/libvold/android_arm64_armv8-a_static/obj/system/vold/model/PublicVolume.o','system/vold/vold/android_arm64_armv8-a/unstripped/vold'])]
# Expose only selected action rows and schema field names, never unrelated inputs.
r=dict(path=str(p),row_count=len(rows),first_row_keys=sorted(rows[0]) if rows else [],selected_rows=selected)
local=P/'siso_localexec'
if local.is_file():
 lines=[]
 with local.open() as f:
  for line in f:
   if any(s in line for s in ['system/bpf/loader/bpfloader/','system/vold/libvold/android_arm64_armv8-a_static/obj/system/vold/model/PublicVolume.o','system/vold/vold/android_arm64_armv8-a/unstripped/vold']):lines.append(line[:8000])
 r['selected_localexec_lines']=lines
with (R/'evidence/selected-frozen-metrics.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/selected-frozen-metrics.json').write_text(r);print(r[:18000])
