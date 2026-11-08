#!/usr/bin/env python3
"""Mechanical API migration in probe copies only. No fake battery/accessory implementations."""
import re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for p in (root/'sources/power-probe').glob('*.[ch]'):
 s=p.read_text()
 for a,b in [('kal_bool','bool'),('kal_uint32','unsigned int'),('kal_int32','int'),('kal_uint16','unsigned short'),('kal_uint8','unsigned char'),('KAL_FALSE','false'),('KAL_TRUE','true'),('FALSE','false'),('TRUE','true')]:s=re.sub(r'\b'+a+r'\b',b,s)
 s=s.replace('<mt-plat/mt_boot.h>','<mt-plat/mtk_boot.h>')
 s=s.replace('battery_log(BAT_LOG_CRTI,','pr_notice(').replace('battery_log(BAT_LOG_FULL,','pr_debug(')
 p.write_text(s)
