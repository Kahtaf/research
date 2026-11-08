from pathlib import Path
import subprocess
O=Path('/srv/android/asus-linux49-pmic-stage-capture-20261108-a1ff82b1/out')
for n in ['arch/arm64/kernel/asus_retained_trace.o','vmlinux']:
 print(n)
 s=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(O/n)],text=True)
 for l in s.splitlines():
  if l.split()[-1] in ['pm_init','pm_header','pm_property','pm_record','pm_ps_field','trace_init','cap_init']:print(l)
