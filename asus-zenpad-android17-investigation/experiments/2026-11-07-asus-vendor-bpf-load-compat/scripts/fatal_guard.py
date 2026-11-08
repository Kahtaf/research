from pathlib import Path
import json,os,signal,time,datetime
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');O=R/'run-runtime';started=json.loads((O/'started.json').read_text());pid=started['owned_qemu_pid'];deadline=time.monotonic()+610
# Supplement the existing banner/panic/init supervisor for explicit native/framework fatal lines.
while not (O/'status.json').exists() and time.monotonic()<deadline:
 t=(O/'serial.log').read_text(errors='replace')
 fatal=next((line for line in t.splitlines() if 'Fatal signal ' in line or 'FATAL EXCEPTION IN SYSTEM PROCESS' in line or '*** FATAL EXCEPTION IN SYSTEM PROCESS' in line),None)
 if fatal:
  d=dict(first_fatal_line=fatal,detected_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),owned_qemu_pid=pid,action='SIGKILL only the QEMU launched by this spike',poll_seconds=0.1)
  try:os.kill(pid,signal.SIGKILL);d['signal_sent']=True
  except ProcessLookupError:d['signal_sent']=False
  (O/'explicit-fatal-guard.json').write_text(json.dumps(d,indent=2));break
 time.sleep(0.1)
