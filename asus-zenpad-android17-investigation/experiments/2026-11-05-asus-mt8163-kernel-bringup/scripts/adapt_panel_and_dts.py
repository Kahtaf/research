#!/usr/bin/env python3
import hashlib,json,re
from pathlib import Path
from source_edits import ROOT,SOURCE,replace
old=ROOT.parent/'2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18'
header='include/dt-bindings/soc/mt8163-md32.h';target=SOURCE/header
assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((old/header).read_bytes())
replace('arch/arm64/boot/dts/mediatek/asus-p00a.dts','#include "mt8163.dtsi"','#include "mt8163.dtsi"\n#include <dt-bindings/soc/mt8163-md32.h>')
p=SOURCE/'drivers/misc/mediatek/lcm/z380m_kd_rm68200g01/z380m_kd_rm68200g01.c';s=p.read_text()
for name in ['LCM_UTIL_FUNCS','LCM_PARAMS','LCM_DRIVER']:
 s=re.sub(r'\b'+name+r'\b','struct '+name,s)
p.write_text(s)
provenance=ROOT/'evidence/asus-import-provenance.json';data=json.loads(provenance.read_text());data.append(dict(original=str(old/header),target=header,sha256=hashlib.sha256((old/header).read_bytes()).hexdigest()));provenance.write_text(json.dumps(data,indent=2)+'\n')
print('Adapted legacy panel struct names and imported MD32 DT binding (semaphore 7 preserved).')
