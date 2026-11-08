#!/usr/bin/env python3
from pathlib import Path
import re, subprocess, json, shutil, hashlib, sys
r=Path(__file__).resolve().parents[1]; b=r/'evidence/base'; s=r/'staged'
o=r/'evidence/host';o.mkdir(exist_ok=True)
h=o/'include'
(h/'linux').mkdir(parents=True,exist_ok=True);(h/'mach').mkdir(exist_ok=True)
text=(b/'include/linux/power_supply.h').read_text()
part=text[text.index('enum {'):text.index('struct device_node;')]
(h/'linux/power_supply.h').write_text('#pragma once\n#include <stdint.h>\n'+part)
(h/'linux/errno.h').write_text('#include <errno.h>\n')
(h/'linux/kernel.h').write_text('#ifndef ARRAY_SIZE\n#define ARRAY_SIZE(a) (sizeof(a)/sizeof((a)[0]))\n#endif\n')
shutil.copy(b/'drivers/misc/mediatek/include/mt-plat/mt8163/include/mach/upmu_hw.h',h/'mach/upmu_hw.h')
source=s/'drivers/misc/mediatek/power/mt8163/asus_p00a'
cmd=['clang','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-sign-compare','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(h),'-I'+str(s/'include'),'-I'+str(source),str(r/'tests/host_battery.c'),'-o',str(o/'host_battery')]
build=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(o/'compile.log').write_text(build.stdout)
result={'compiler':subprocess.check_output(['clang','--version'],text=True).splitlines()[0],'command':cmd,'compile_returncode':build.returncode,'scope':'host compilation of exact production additions with simulated kernel/transport; NOT a kernel build'}
if not build.returncode:
    run=subprocess.run([str(o/'host_battery')],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (o/'run.log').write_text(run.stdout);result.update(run_returncode=run.returncode,output=run.stdout)
(r/'evidence/host-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(build.stdout or result.get('output'));sys.exit(build.returncode or result.get('run_returncode',1))
