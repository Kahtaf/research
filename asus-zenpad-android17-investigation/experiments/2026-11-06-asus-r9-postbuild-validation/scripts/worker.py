"""Invoke only the owned validator; all helpers come from the sealed kit."""
from pathlib import Path
import fcntl
import importlib.util
import json
import os
import sys

ROOT = Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
OWN = Path('/srv/android/asus-r9-postbuild-validation-r1')
sys.path.insert(0, str(ROOT / 'scripts'))
from integrate import need, sha, read, write

fd = int(os.environ['REVIEWED_BUILD_LOCK_FD'])
need(os.fstat(fd).st_ino == 15018964, 'Wrong inherited lock inode')
fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
source = OWN / 'scripts/validate_completed_product.py'
need(sha(source) == '526aae8dbf2af756689718ca37fe3bfd64ddace845ab3a3b90af6479198430f6', 'Owned validator source drift')
spec = importlib.util.spec_from_file_location('owned_validator', source)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
try:
    validator.validate(ROOT)
finally:
    raw = OWN / 'validation/system-partition.raw'
    if raw.is_file() and raw.stat().st_size == 3753902080:
        from verify_product_r3 import installed
        plan = read(ROOT / 'inputs/plan.json')
        p = Path(plan['product_out'])
        receipt = installed(p, 'system/lib/liblog.so', raw,
                            Path(plan['aosp']) / 'out/host/linux-x86/bin/debugfs',
                            '473bb94ce06678bffd72eb2c34d2f105d540cdedba6e5cc9c4f2c2d073449f9d')
        write(OWN / 'liblog-final-system-bytes.json', receipt)
print(json.dumps({'host_validation_complete': True, 'flash_ready': False}), flush=True)
