#!/usr/bin/env python3
"""Bounded offline Kbuild run. Execute inside the Linux audit container."""
import argparse,json,os,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('config');p.add_argument('--label',required=True);p.add_argument('--target',default='Image.gz-dtb');p.add_argument('--timeout',type=int,default=1200);p.add_argument('--out-label');p.add_argument('--resume',action='store_true');a=p.parse_args()
root=Path('/work');source=root/'sources/kernel';out=root/'build'/(a.out_label or a.label);logs=root/'evidence'/a.label
out.mkdir(parents=True,exist_ok=True);logs.mkdir(parents=True,exist_ok=True)
base=['make','-C',str(source),'O='+str(out),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','KBUILD_BUILD_USER=asus-port','KBUILD_BUILD_HOST=offline-builder','KBUILD_BUILD_VERSION=1','KBUILD_BUILD_TIMESTAMP=Thu Nov 5 00:00:00 UTC 2026']
results=[]
steps=[] if a.resume else [('defconfig',[a.config],120)]
steps += [('build',['-j4',a.target],a.timeout)]
for label,args,timeout in steps:
 command=base+args;start=time.monotonic()
 with (logs/(label+'.log')).open('w') as f:
  try:r=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,timeout=timeout);code=r.returncode
  except subprocess.TimeoutExpired:code='timeout'
 results.append(dict(step=label,command=command,exit_code=code,elapsed_seconds=round(time.monotonic()-start,2)))
 (logs/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(label,code,flush=True)
 if code!=0:
  print('\n'.join((logs/(label+'.log')).read_text(errors='replace').splitlines()[-35:]));break
