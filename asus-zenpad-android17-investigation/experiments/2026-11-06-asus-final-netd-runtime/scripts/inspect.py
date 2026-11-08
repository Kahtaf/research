from pathlib import Path
import subprocess as s,json,os,resource
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
N=Path('/srv/android/asus-network-runtime');P=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106');F=Path('/srv/android/asus-final-bpf-runtime-20261106')
for p in [P/'source/fixture_init_r2.c',P/'supplement-qualified-r2/manifest.json',N/'source/guest_init.c']:
 print('FILE',p);print(p.read_text()[:18000] if p.exists() else 'absent')
for folder in [N/'inputs/Connectivity',N/'inputs/headers',P/'source',P/'supplement-qualified-r2']:
 print('SEARCH',folder)
 
 import re
 found=[]
 for p in folder.rglob('*'):
  if p.is_file() and p.suffix in ['.h','.c','.cpp','.json']:
   for i,line in enumerate(p.read_text(errors='replace').splitlines()):
    if re.search(r'ro\.(build|board|bpf)|Get.*Property|android_get_device_api_level|aconfig|sdk_full',line):found.append(f'{p}:{i+1}:{line}')
 print('\n'.join(found)[:24000])
print('PROPS',s.run(['find',str(F/'capture'),'-name','*prop*'],capture_output=True,text=True).stdout)
print('COMPILE',s.run(['find',str(P/'evidence'),'-iname','*compile*'],capture_output=True,text=True).stdout)
