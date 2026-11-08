from pathlib import Path
import json,datetime
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');p=R/'run-runtime/status.json'
if p.exists(): print('FINAL_STATUS',p.read_text())
p=R/'run-runtime/serial.log';t=p.read_text(errors='replace');print('SERIAL_BYTES',p.stat().st_size);lines=t.splitlines();keys=['Activated',' all packages','On-device signing done','NetBpfLoad: done','Platform BpfLoader','CRITICAL FAILURE','Fatal signal','FATAL EXCEPTION','zygote','system_server','bpf.progs_loaded','apexd.status=','wait_for_prop','Kernel panic']
a=[l for l in lines if any(k in l for k in keys)];print('\n'.join(a[-22:]));print('LAST',lines[-1]);p=R/'evidence/runtime-resume-result.json'
if p.exists():print(p.read_text())
