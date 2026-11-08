from pathlib import Path
import json,datetime
R=Path('/srv/android/asus-android-runtime-network-parity-20261107');E=R/'evidence'
print(datetime.datetime.now(datetime.timezone.utc).isoformat())
for n in ['startup-pipeline-result.json']:
 p=E/n
 if p.exists():print(n,p.read_text())
for n in ['build-runner.log','startup-pipeline.log']:
 p=E/n
 if p.exists():
  with p.open('rb') as f:f.seek(max(0,p.stat().st_size-1400));print(n,p.stat().st_size,f.read().decode(errors='replace'))
p=R/'run-runtime/serial.log'
if p.exists():
 text=p.read_text(errors='replace');need=['odsign','odrefresh','NetBpfLoad','bpf.progs_loaded','zygote','apexd.status','exited with','panic','reboot_on_failure']
 print('serial bytes',p.stat().st_size);print('\n'.join(x for x in text.splitlines() if any(n in x for n in need))[-3500:])
