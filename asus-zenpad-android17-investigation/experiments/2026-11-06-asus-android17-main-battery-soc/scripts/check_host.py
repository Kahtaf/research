#!/usr/bin/env python3
"""Compile/run exact production logic on the Mac; not an ARM64 kernel build."""
from pathlib import Path
import subprocess,json,concurrent.futures,hashlib,sys
R=Path(__file__).resolve().parents[1];O=R/'evidence/host';S=R/'staged';B=R/'source/kernel-after-measurement'
subprocess.run([sys.executable,str(R/'scripts/prepare_host.py')],check=True)
inc=[O/'include',S/'include',S/'drivers/misc/mediatek/include',S/'drivers/power/supply/mediatek/battery',S/'drivers/misc/mediatek/power/mt8163/asus_p00a',B/'drivers/misc/mediatek/power/mt8163/asus_p00a']
cflags=['-std=gnu11','-Wall','-Wextra','-Werror','-Wno-sign-compare','-Wno-unused-parameter','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-DCONFIG_ASUS_P00A_MAIN_BATTERY_SOC']+['-I'+str(p) for p in inc]
dev=R/'integration/device/asus/p00a/health'
commands={
 'model':['clang']+cflags+[str(R/'tests/host_model.c'),'-o',str(O/'host_model')],
 'measurement':['clang']+cflags+[str(O/'host_measurement.c'),'-o',str(O/'host_measurement')],
 'health':['clang++','-std=c++17','-Wall','-Wextra','-Werror','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(O/'include'),'-I'+str(dev),str(R/'tests/host_health.cpp'),str(dev/'BatterySnapshot.cpp'),'-o',str(O/'host_health')]
}
def check(item):
 name,cmd=item;build=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(O/(name+'-compile.log')).write_text(build.stdout)
 result={'command':cmd,'compile_returncode':build.returncode}
 if not build.returncode:
  run=subprocess.run([str(O/('host_'+name))]+([str(O/'health-fixture')] if name=='health' else []),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  (O/(name+'-run.log')).write_text(run.stdout);result.update(run_returncode=run.returncode,output=run.stdout)
 return name,result
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: results=dict(pool.map(check,commands.items()))
report={'scope':'Host Clang with ASan/UBSan; exact staged logic and independently extracted ASUS oracle, simulated transports/binder/clock; NOT an ARM64 kernel or Android build','compiler':subprocess.check_output(['clang','--version'],text=True).splitlines()[0],'tests':results}
report['tested_inputs']={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['staged','integration/platform','integration/device'] for p in (R/folder).rglob('*') if p.is_file()}
(R/'evidence/host-checks.json').write_text(json.dumps(report,indent=2)+'\n')
for k,v in results.items():
 print(k, v.get('output') or (O/(k+'-compile.log')).read_text())
sys.exit(any(v['compile_returncode'] or v.get('run_returncode',1) for v in results.values()))
