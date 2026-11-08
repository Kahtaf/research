from pathlib import Path
import json,os,signal,datetime
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');O=R/'run-runtime';lines=(O/'serial.log').read_text(errors='replace').splitlines();keys=['CRITICAL','FATAL','Fatal','fatal','surfaceflinger','bpfloader','BpfLoader','bpf.progs_loaded','system_server'];a=[(i,l) for i,l in enumerate(lines,1) if any(k in l for k in keys)];print('\n'.join(f'{i}: {l}' for i,l in a[-100:]))
# SurfaceFlinger is an essential framework service and explicitly exiting here.
# Stop this owned startup at the newly observed framework boundary, never retry.
fatal=next((l for l in lines if "Service 'surfaceflinger'" in l and ('exited with status' in l or 'received signal' in l)),None)
if fatal and not (O/'status.json').exists():
 d=dict(first_fatal_line=fatal,detected_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),owned_qemu_pid=json.loads((O/'started.json').read_text())['owned_qemu_pid'],action='Stop owned QEMU at explicit SurfaceFlinger framework failure; no retry',detection_limitation='SurfaceFlinger service-exit boundary was recognized during progress collection; automatic banner/native-fatal patterns did not match it')
 try:os.kill(d['owned_qemu_pid'],signal.SIGKILL);d['signal_sent']=True
 except ProcessLookupError:d['signal_sent']=False
 (O/'framework-boundary-stop.json').write_text(json.dumps(d,indent=2));print('STOP',json.dumps(d))
