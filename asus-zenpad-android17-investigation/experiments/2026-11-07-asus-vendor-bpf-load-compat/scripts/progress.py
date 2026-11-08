from pathlib import Path
import json
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107')
for n in ['evidence/startup-pipeline-result.json','run-runtime/status.json','run-runtime/started.json']:
 p=R/n
 if p.exists(): print(n,p.read_text())
p=R/'evidence/startup-pipeline.log';print('PIPELINE_TAIL',p.read_text(errors='replace')[-2500:])
p=R/'run-runtime/serial.log'
if p.exists():
 t=p.read_text(errors='replace');print('SERIAL_BYTES',p.stat().st_size);print('\n'.join(t.splitlines()[-14:]))
