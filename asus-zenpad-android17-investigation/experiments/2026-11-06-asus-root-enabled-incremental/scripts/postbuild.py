"""Run exact scoped host checks against the new native image outputs."""
from pathlib import Path
import importlib.util
import os
import resource
import sys

resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
ROOT = Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
OWN = Path('/srv/android/asus-root-enabled-incremental-r1')
sys.path.insert(0, str(ROOT / 'scripts'))
from integrate import read, write, need, sha

def load(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

pins = read(OWN / 'inputs/owned-code-pins.json')
for relative, digest in pins.items():
    need(sha(OWN / relative) == digest, 'Owned execution code drift: ' + relative)
need(os.fstat(int(os.environ['REVIEWED_BUILD_LOCK_FD'])).st_ino == 15018964, 'Inherited lock drift')
plan = read(OWN / 'inputs/plan.json')
config_path = Path(plan['aosp']) / 'out/soong/.intermediates/build/soong/product_config/product_config.json'
config = read(config_path)
need(config['ProductNotDebuggableInUserdebug'] is False and config['Debuggable'] is True and config['Eng'] is False,
     'Actual generator is not root-enabled userdebug')
write(OWN / 'attempt/generator-readback.json', {'path': str(config_path), 'sha256': sha(config_path),
      'ProductNotDebuggableInUserdebug': config['ProductNotDebuggableInUserdebug'],
      'Debuggable': config['Debuggable'], 'Eng': config['Eng']})
load('continuation', OWN / 'scripts/continuation.py')
load('integrate', OWN / 'scripts/integrate.py')
load('verify_full_images', OWN / 'scripts/verify_full_images.py')
load('cache_lineage', OWN / 'scripts/native_adapter.py')
load('verify_product_r3', OWN / 'scripts/verify_product_r3.py')
load('bootformat', OWN / 'scripts/owned_bootformat.py')
validator = load('root_enabled_validator', OWN / 'scripts/validate_completed_product.py')
validator.validate(ROOT)

from verify_product_r3 import installed
p = Path(plan['product_out'])
raw = OWN / 'validation/system-partition.raw'
write(OWN / 'validation/liblog-final-bytes.json', installed(p, 'system/lib/liblog.so', raw,
      Path(plan['aosp']) / 'out/host/linux-x86/bin/debugfs',
      '473bb94ce06678bffd72eb2c34d2f105d540cdedba6e5cc9c4f2c2d073449f9d'))
import package_full_boot as packager
ram = packager.components((p / 'boot.img').read_bytes())[2]
entries = packager.parse_cpio(packager.ungzip(ram)[0])
property_files = {}
for name, (_, _, _, data) in entries.items():
    if name.endswith(('.prop', 'prop.default', 'default.prop')):
        property_files[name] = [line for line in data.decode().splitlines()
                                if line.partition('=')[0].strip() in ('ro.secure', 'ro.debuggable', 'ro.adb.secure')]
write(OWN / 'validation/actual-boot-property-layout.json', {'property_files': property_files,
      'has_embedded_property_file': bool(property_files), 'ramdisk_compressed_sha256': __import__('hashlib').sha256(ram).hexdigest(),
      'scope': 'First-stage BOOT archive inspected directly; SYSTEM property bytes separately checked by root-route verifier; no runtime property claim'})
