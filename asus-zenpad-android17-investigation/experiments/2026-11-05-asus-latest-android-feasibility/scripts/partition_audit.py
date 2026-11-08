#!/usr/bin/env python3
import json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
serial='DEVICE_SERIAL_REDACTED'
def shell(cmd):return subprocess.check_output(['adb','-s',serial,'shell',cmd],text=True,timeout=45)
assert shell('getprop ro.product.device').strip()=='P00A_2'
rows=[]
for line in shell('for p in /sys/class/block/mmcblk0p*; do echo "$(cat $p/uevent | sed -n s/PARTNAME=//p) $(cat $p/start) $(cat $p/size)"; done').splitlines():
 name,start,size=line.split();rows.append(dict(name=name,start_sector=int(start),sectors=int(size),offset_bytes=int(start)*512,size_bytes=int(size)*512))
rows.sort(key=lambda r:r['start_sector'])
scatter=dict(line.split() for line in (root/'sources/stock-firmware/scatter.txt').read_text().splitlines() if len(line.split())==2)
for r in rows:
 if r['name'] in scatter:
  r['firmware_scatter_offset']=int(scatter[r['name']],16);r['scatter_matches_live']=r['firmware_scatter_offset']==r['offset_bytes']
(root/'evidence/live-partition-layout.json').write_text(json.dumps(rows,indent=2)+'\n')
for r in rows:
 if r['name'] in ['boot','recovery','system','userdata']:print(r)
status=shell('id; command -v su; getprop ro.boot.verifiedbootstate; getenforce; pm list packages -e com.google; pm list packages -d com.google; pm list packages -d com.asus')
(root/'evidence/device/final-readonly-check.txt').write_text(status)
print(status)
