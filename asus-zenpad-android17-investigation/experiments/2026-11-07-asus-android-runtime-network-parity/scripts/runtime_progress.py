from pathlib import Path
import json,datetime
R=Path('/srv/android/asus-android-runtime-network-parity-20261107');print(datetime.datetime.now(datetime.timezone.utc).isoformat())
p=R/'run-runtime/serial.log'
if p.exists():
 t=p.read_text(errors='replace');lines=t.splitlines();print('serial bytes',p.stat().st_size);need=['Wait for property','starting service \'odsign\'','starting service \'bpfloader\'','NetBpfLoad','bpf.progs_loaded','starting service \'zygote\'','starting service \'netd\'','Kernel panic','reboot_on_failure','sys.powerctl','All packages activated','Activated 39','zygote exited','Service \'bpfloader\'']
 print('\n'.join(x for x in lines if any(n in x for n in need))[-6000:]);print('TAIL');print('\n'.join(lines[-4:]))
for n in ['run-runtime/status.json','evidence/startup-pipeline-result.json']:
 p=R/n
 if p.exists():print(n,p.read_text())
