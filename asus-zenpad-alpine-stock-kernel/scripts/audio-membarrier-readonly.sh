set -eu
python3 - <<'PY'
from pathlib import Path
symbols=Path('/proc/kallsyms').read_text()
matches=[line for line in symbols.splitlines() if line.split()[-1:] == ['sys_membarrier']]
print('SYS_MEMBARRIER_KERNEL_SYMBOL_COUNT',len(matches))
log=Path('/tmp/asus-media-trial/browser-debug.log').read_text(errors='replace')
for phrase in ('seccomp sandbox violation','Assertion failed','terminate called'):
 print('DIAGNOSTIC_LOG_PHRASE',repr(phrase),phrase in log)
print('PRIVATE_FULL_LOG_BYTES',Path('/tmp/asus-media-trial/browser-debug.log').stat().st_size)
PY
