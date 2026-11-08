#!/usr/bin/env python3
from pathlib import Path
import subprocess,json,sys,hashlib
R=Path(__file__).resolve().parents[1];S=R/'staged';O=R/'evidence/host'
subprocess.run([sys.executable,str(R/'scripts/prepare_tests.py')],check=True)
inc=[O/'include',S/'include',S/'drivers/misc/mediatek/power/mt8163/asus_p00a',S/'drivers/power/supply/mediatek/battery']
flags=['-std=gnu11','-Wall','-Wextra','-Werror','-Wno-sign-compare','-Wno-unused-parameter','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-DCONFIG_ASUS_P00A_MAIN_BATTERY_SOC']+['-I'+str(p) for p in inc]
results={}
for n in ['charging','model','bc12']:
 source=R/'tests'/('host_'+n+'.c')
 if not source.exists():continue
 cmd=['clang']+flags+[str(source),'-o',str(O/('host_'+n))]
 build=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(O/(n+'-compile.log')).write_text(build.stdout)
 result={'command':cmd,'compile_returncode':build.returncode}
 if not build.returncode:
  run=subprocess.run([str(O/('host_'+n))],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  (O/(n+'-run.log')).write_text(run.stdout);result.update(run_returncode=run.returncode,output=run.stdout)
 results[n]=result
 print(n,result.get('output',build.stdout))
report={'scope':'Host ASan/UBSan only, fake regmaps/time; not a target kernel build','tests':results,'compiler':subprocess.check_output(['clang','--version'],text=True).splitlines()[0],'tested_source_sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in S.rglob('*') if p.is_file()}}
(R/'evidence/host-checks.json').write_text(json.dumps(report,indent=2)+'\n')
sys.exit(any(x['compile_returncode'] or x.get('run_returncode',1) for x in results.values()))
