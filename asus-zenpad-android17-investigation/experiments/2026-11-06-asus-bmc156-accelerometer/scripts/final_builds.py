from pathlib import Path
import subprocess,os
R=Path('/srv/android/asus-bmc156-accelerometer-r1')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
for name in ['build_kernel.py','build_hal.py','test_kernel_math.py','test_hal.py','test_registration.py','test_core_state.py']:
 p=subprocess.run(['python3',str(R/'scripts'/name)],capture_output=True,text=True)
 (R/'evidence'/('final-'+name+'.log')).write_text(p.stdout+p.stderr)
 print(name,'EXIT',p.returncode,(p.stdout+p.stderr)[-2000:],flush=True)
 assert p.returncode==0
