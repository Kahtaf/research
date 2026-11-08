#!/usr/bin/env python3
"""Stream actual sysfs property contents; sysfs stat sizes cannot be trusted by adb pull."""
import base64,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'evidence/live-device-tree';out.mkdir(exist_ok=True)
serial='DEVICE_SERIAL_REDACTED'
assert subprocess.check_output(['adb','-s',serial,'shell','getprop ro.product.device'],text=True).strip()=='P00A_2'
command='find /sys/firmware/devicetree/base/ -type f | while read p; do printf "@BEGIN %s\\n" "$p"; base64 "$p"; printf "\\n@END\\n"; done'
r=subprocess.run(['adb','-s',serial,'exec-out','sh','-c',command],capture_output=True,timeout=180)
(root/'evidence/live-dt-stream.stderr').write_bytes(r.stderr)
assert r.returncode==0,r.stderr.decode(errors='replace')
rows=[]
for block in r.stdout.split(b'@BEGIN ')[1:]:
 path,body=block.split(b'\n',1);encoded,end=body.split(b'@END',1)
 rel=path.decode().removeprefix('/sys/firmware/devicetree/base/');dest=out/rel
 data=base64.b64decode(encoded);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);rows.append(dict(path=rel,bytes=len(data)))
assert len(rows)>100 and (out/'compatible').read_bytes().startswith(b'mediatek,mt8163')
(root/'evidence/live-dt-index.json').write_text(json.dumps(dict(properties=len(rows),total_bytes=sum(r['bytes'] for r in rows),files=rows),indent=2)+'\n')
print('Collected actual live DT:',len(rows),'properties')
