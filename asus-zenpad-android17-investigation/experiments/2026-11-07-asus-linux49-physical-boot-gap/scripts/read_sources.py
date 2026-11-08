#!/usr/bin/env python3
"""Fetch only explicit public source files over the existing SSH helper."""
from pathlib import Path
import importlib.util, json, gzip, hashlib, sys
sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent
spec=importlib.util.spec_from_file_location('remote',WORK/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
files=['arch/arm64/kernel/cpu_ops.c','arch/arm64/kernel/setup.c','arch/arm64/kernel/head.S',
       'arch/arm64/mm/init.c','arch/arm64/kernel/time.c','arch/arm64/kernel/irq.c',
       'drivers/firmware/psci.c','drivers/clocksource/mtk_timer.c',
       'drivers/clocksource/arm_arch_timer.c','drivers/irqchip/irq-gic.c',
       'drivers/clk/mediatek/clk-mt8163.c','drivers/clk/mediatek/Makefile',
       'drivers/misc/mediatek/base/power/mt8163/mt_psci.c',
       'drivers/misc/mediatek/base/power/mt8163/Makefile',
       'arch/arm64/boot/dts/mediatek/mt8163.dtsi',
       'arch/arm64/boot/dts/mediatek/asus-p00a.dts']
script='''from pathlib import Path
import json
root=Path('/srv/android/asus-bmc156-full-kernel-r1/kernel')
files=FILES
result={}
for f in files:
 p=root/f
 if p.is_file(): result[f]=p.read_text()
print(json.dumps(result))
'''.replace('FILES',repr(files))
result=json.loads(remote.run(script))
baseline=json.loads(gzip.decompress((WORK/'2026-11-06-asus-bmc156-full-kernel/evidence/r5-source-manifest.json.gz').read_bytes()))
receipts={}
for f,t in result.items():
 p=ROOT/'source'/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t)
 digest=hashlib.sha256(t.encode()).hexdigest()
 receipts[f]={'sha256':digest,'r5_sha256':baseline.get(f),'matches_r5':digest==baseline.get(f)}
(ROOT/'evidence/source-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
print(json.dumps(receipts,indent=2))
print('absent',sorted(set(files)-set(result)))
