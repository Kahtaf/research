"""Check the two copied input mappings in installed files and real SYSTEM ext4."""
from pathlib import Path
import subprocess
from integrate import INPUT_FILES, need, sha
import hashlib

INSTALLED = {
    'system/vendor/usr/idc/Goodix_Capacitive_TouchScreen.idc': INPUT_FILES['input/Goodix_Capacitive_TouchScreen.idc'],
    'system/vendor/usr/keylayout/mtk-kpd.kl': INPUT_FILES['input/mtk-kpd.kl'],
}

def verify(product_out, raw_image=None, debugfs=None):
    need(bool(raw_image) == bool(debugfs), 'Both raw SYSTEM and debugfs required')
    before = raw_image.stat() if raw_image else None
    checks = []
    for rel, expected in INSTALLED.items():
        path = Path(product_out) / rel
        need(path.is_file() and not path.is_symlink() and path.stat().st_size < 4096,
             'Input mapping missing or invalid: ' + rel)
        need(sha(path) == expected, 'Installed input mapping bytes differ: ' + rel)
        if raw_image:
            result = subprocess.run([str(debugfs), '-R', 'cat /' + rel, str(raw_image)],
                                    capture_output=True, timeout=15)
            need(result.returncode == 0 and hashlib.sha256(result.stdout).hexdigest() == expected,
                 'SYSTEM input mapping bytes differ: ' + rel)
        checks.append({'path': rel, 'sha256': expected, 'final_ext4_verified': bool(raw_image)})
    if raw_image:
        after = raw_image.stat()
        need((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
             'SYSTEM changed during input mapping checks')
    return {'checked': checks, 'physical_input_verified': False}
