"""Invoke only the owned validator; all helpers come from the sealed kit."""
from pathlib import Path
import fcntl
import importlib.util
import json
import os
import sys

ROOT = Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
OWN = Path('/srv/android/asus-r9-postbuild-validation-r3')
sys.path.insert(0, str(ROOT / 'scripts'))
from integrate import need, sha, read, write

fd = int(os.environ['REVIEWED_BUILD_LOCK_FD'])
need(os.fstat(fd).st_ino == 15018964, 'Wrong inherited lock inode')
fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
source = OWN / 'scripts/validate_completed_product.py'
need(sha(source) == '0fb59d0ba37059f64a04ed1825b8245b0049915c68005f8b5f3bed854d5834a5', 'Owned validator source drift')
need(sha(OWN / 'reuse-and-sensor-metadata.json') == 'c58b4ff873d8692c0c39f641bec997b09235296434b655882cc17a2a5745d28a', 'Reuse receipt drift')
helper = OWN / 'scripts/verify_product_r3.py'
need(sha(helper) == 'ef1567d7ee0d31e6f2bb0c3c56191a02719a9b9f65552824d83867a458fee00f', 'Owned provenance helper drift')
helper_spec = importlib.util.spec_from_file_location('verify_product_r3', helper)
helper_module = importlib.util.module_from_spec(helper_spec)
sys.modules['verify_product_r3'] = helper_module
helper_spec.loader.exec_module(helper_module)
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
