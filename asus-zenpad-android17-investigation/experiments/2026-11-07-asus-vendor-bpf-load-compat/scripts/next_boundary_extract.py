from pathlib import Path
import json
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');E=R/'evidence';a=(E/'public-report-raw.txt').read_text(errors='replace').splitlines();keys=['CANNOT LINK','hwcomposer','SurfaceFlinger','surfaceflinger','FATAL','Fatal','ProcessState','system_server'];out=[]
for i,l in enumerate(a):
 if any(k in l for k in keys) and l not in out:out.append(l)
(E/'next-boundary-public.txt').write_text('\n'.join(out)+'\n');print('\n'.join(out[:35]));print('UNIQUE_BOUNDARY_LINES',len(out))
lines=(R/'run-runtime/serial.log').read_text().splitlines();firsthw=next(l for l in lines if "Service 'vendor.hwcomposer-2-1'" in l and 'exited with status 1' in l);firstzyg=next(l for l in lines if "starting service 'zygote'" in l);last=lines[-1]
d=json.loads((E/'result.json').read_text());d['bpf_progs_loaded']={'value':'1','source':'genuine init property wait already set at 388.743887s','line':next(l for l in lines if 'start_waiting_for_property("bpf.progs_loaded", "1"): already set' in l),'shell_observer_reads':'empty; do not infer absence from these reads'};d['next_boundary']={'first_hwcomposer_exit':firsthw,'first_zygote_start':firstzyg,'last_guest_line':last,'root_cause':'not isolated; HWC exit triggers SurfaceFlinger and zygote restarts','system_server_or_framework_ready':'not established'};(E/'result.json').write_text(json.dumps(d,indent=2));print(json.dumps(d['next_boundary'],indent=2))
