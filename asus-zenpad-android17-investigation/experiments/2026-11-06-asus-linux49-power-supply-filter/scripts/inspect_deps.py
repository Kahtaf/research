from pathlib import Path
import json
O=Path('/srv/android/asus-linux49-power-supply-filter-20261106');print((O/'artifacts/postimage.d').read_text());print('RUN4', (O/'run-r4/result.json').read_text() if (O/'run-r4/result.json').exists() else 'notcomplete');
if (O/'run-r4/serial.log').exists():
 print('\n'.join(l for l in (O/'run-r4/serial.log').read_text(errors='replace').splitlines() if any(x in l for x in ['HOST_ORACLE','PROG_LOAD','SO_ATTACH','KERNEL_ORACLE','FILTER_TEST_EXIT','back-edge'])))
