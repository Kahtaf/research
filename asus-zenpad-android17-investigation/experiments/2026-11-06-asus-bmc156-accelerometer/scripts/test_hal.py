from pathlib import Path
import subprocess,resource,os,json
R=Path('/srv/android/asus-bmc156-accelerometer-r1');H=R/'sdk/headers';O=R/'hal-out'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
cmd=['gcc','-std=gnu11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=undefined,bounds','-pthread']
for p in [H/'hardware/libhardware/include_all',H/'system/core/libcutils/include',H/'system/core/libsystem/include',R/'source/hal']:cmd+=['-I'+str(p)]
cmd+=[str(R/'source/tests/test_hal.c'),str(R/'source/hal/accel_protocol.c'),'-o',str(O/'test_hal')]
p=subprocess.run(cmd,capture_output=True,text=True);print(p.stdout,p.stderr);assert p.returncode==0

def limits():resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(30,30))
p=subprocess.run([str(O/'test_hal')],capture_output=True,text=True,preexec_fn=limits,timeout=35);print(p.stdout,p.stderr)
(R/'evidence/hal-callback-tests.json').write_text(json.dumps(dict(command=cmd,exit=p.returncode,stdout=p.stdout,stderr=p.stderr,one_cpu=True,address_space_bytes=1024**3),indent=2)+'\n');assert p.returncode==0
