#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];old=root.parent/'2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18';out=root/'sources/power-probe';out.mkdir(exist_ok=True)
rows=[]
for name in ['bq25896.c','bq25896.h','charging_hw_bq25896.c']:
 p=old/'drivers/misc/mediatek/power/mt8163'/name;data=p.read_bytes();(out/name).write_bytes(data);rows.append(dict(source=str(p),file=name,sha256=hashlib.sha256(data).hexdigest()))
(out/'Makefile').write_text('obj-m += bq25896.o charging_hw_bq25896.o\nccflags-y += -DCONFIG_Z380M\nccflags-y += -I$(srctree)/drivers/misc/mediatek/include -I$(srctree)/drivers/misc/mediatek/include/mt-plat -I$(srctree)/drivers/misc/mediatek/include/mt-plat/mt8163/include\n')
(root/'evidence/power-source-provenance.json').write_text(json.dumps(rows,indent=2)+'\n')
