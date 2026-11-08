from pathlib import Path
import json,os,signal,datetime
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');O=R/'run-runtime';lines=(O/'serial.log').read_text(errors='replace').splitlines();fatal=next((l for l in lines if "Service 'surfaceflinger'" in l and 'received SIGKILL' in l),None);assert fatal
if not (O/'status.json').exists():
 d=dict(first_boundary_line=fatal,last_guest_line=lines[-1],detected_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),owned_qemu_pid=json.loads((O/'started.json').read_text())['owned_qemu_pid'],action='Stop owned QEMU at framework restart boundary; no retry',detection_limitation='Automatic critical-banner/native-fatal matchers missed hwcomposer-triggered SurfaceFlinger and zygote restart cycle; stop was delayed')
 try:os.kill(d['owned_qemu_pid'],signal.SIGKILL);d['signal_sent']=True
 except ProcessLookupError:d['signal_sent']=False
 (O/'framework-boundary-stop.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
