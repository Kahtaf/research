#!/bin/bash
set -eo pipefail
cd /srv/android/lineage24
source build/envsetup.sh
lunch lineage_p00a-trunk_staging-userdebug
mkdir -p /srv/android/asus-device-product/logs
build/soong/soong_ui.bash --dumpvars-mode --vars='TARGET_DEVICE PLATFORM_SDK_VERSION PLATFORM_VERSION_LAST_STABLE PRODUCT_BUILD_BOOT_IMAGE PRODUCT_BUILD_RECOVERY_IMAGE PRODUCT_BUILD_SYSTEM_IMAGE PRODUCT_BUILD_VENDOR_IMAGE' > /srv/android/asus-device-product/logs/network-product-vars.txt
python3 - <<'PY'
from pathlib import Path
import shlex
values = {}
for line in Path('/srv/android/asus-device-product/logs/network-product-vars.txt').read_text().splitlines():
    key, sep, value = line.partition('=')
    if sep:
        values[key] = ' '.join(shlex.split(value))
assert values['TARGET_DEVICE'] == 'p00a', values
assert values['PLATFORM_SDK_VERSION'] == '37', values
assert values['PLATFORM_VERSION_LAST_STABLE'] == '17', values
for name in ['BOOT', 'RECOVERY', 'SYSTEM', 'VENDOR']:
    assert values[f'PRODUCT_BUILD_{name}_IMAGE'] == 'false', values
print('ASUS SDK 37 module build; all device image targets remain disabled.')
PY
m -j8 netd netbpfload netd.o
date -u --iso-8601=seconds > /srv/android/asus-device-product/logs/network-build-complete
