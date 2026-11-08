from pathlib import Path
import datetime,json
R=Path('/srv/android/asus-android-runtime-network-parity-20261107');p=R/'run-runtime/serial.log';t=p.read_text(errors='replace');print(datetime.datetime.now(datetime.timezone.utc).isoformat());print('SERIAL_BYTES',p.stat().st_size)
need=['odsign','odrefresh','NetBpfLoad','bpf.progs_loaded','zygote','aconfig','linkerconfig','apexd.status','keystore.module','exited with','panic','PUBLIC_SAMPLE']
lines=[x for x in t.splitlines() if any(n in x for n in need)];print('\n'.join(lines[-65:]));print('TAIL');print(t[-2000:])
