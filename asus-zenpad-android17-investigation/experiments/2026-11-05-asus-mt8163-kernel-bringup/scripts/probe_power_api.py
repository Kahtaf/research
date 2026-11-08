#!/usr/bin/env python3
import json,subprocess,time
from pathlib import Path
root=Path('/work');out=root/'build/power-probe';log=root/'evidence/power-probe';log.mkdir(exist_ok=True)
base=['make','-C','/work/sources/kernel','O='+str(out),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++']
steps=[('defconfig',['asus_p00a_defconfig']),('prepare',['prepare','scripts']),('bq25896',['M=/work/sources/power-probe','bq25896.o']),('charging_hw',['M=/work/sources/power-probe','charging_hw_bq25896.o'])]
rows=[]
for name,args in steps:
 start=time.monotonic()
 with (log/(name+'.log')).open('w') as f:
  r=subprocess.run(base+args,stdout=f,stderr=subprocess.STDOUT,timeout=180)
 rows.append(dict(name=name,command=base+args,exit_code=r.returncode,elapsed_seconds=round(time.monotonic()-start,2)))
 print(name,r.returncode,flush=True)
 if r.returncode and name in ['defconfig','prepare']:break
(log/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
