#!/usr/bin/env python3
import json,subprocess,struct
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'evidence/live-properties';out.mkdir(exist_ok=True)
serial='DEVICE_SERIAL_REDACTED'
def read(path):
 r=subprocess.run(['adb','-s',serial,'exec-out','cat',path],capture_output=True,timeout=30)
 if r.returncode: return dict(path=path,error=r.stderr.decode(errors='replace'))
 name=path.strip('/').replace('/','__');(out/name).write_bytes(r.stdout)
 return dict(path=path,file=name,bytes=len(r.stdout),text=r.stdout.decode(errors='replace').replace('\0',' | '))
identity=read('/proc/device-tree/compatible');assert 'mediatek,mt8163' in identity.get('text','')
paths=['/proc/device-tree/chosen/atag,videolfb','/sys/bus/i2c/devices/0-0014/display_id','/sys/bus/i2c/devices/0-0014/tp_id','/sys/bus/i2c/devices/0-0014/tp_fw_version','/sys/bus/i2c/devices/0-0014/name','/sys/bus/i2c/devices/0-006b/name','/sys/bus/i2c/devices/0-0070/name','/sys/bus/i2c/devices/0-002c/name']
rows=[identity]+[read(p) for p in paths]
(out/'index.json').write_text(json.dumps(rows,indent=2)+'\n')
for r in rows:print(r['path'],r.get('bytes'),repr(r.get('text',r.get('error'))))
