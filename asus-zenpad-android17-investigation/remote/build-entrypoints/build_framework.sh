#!/bin/bash
set -eo pipefail
root=/srv/android/asus-device-product
trap 'result=$?; echo "$result" > "$root/logs/framework-build-exit-status"' EXIT
cd /srv/android/lineage24
source build/envsetup.sh
lunch lineage_p00a-trunk_staging-userdebug
build/soong/soong_ui.bash --dumpvars-mode --vars='TARGET_DEVICE TARGET_ARCH PLATFORM_SDK_VERSION PLATFORM_VERSION_LAST_STABLE PRODUCT_BUILD_BOOT_IMAGE PRODUCT_BUILD_RECOVERY_IMAGE PRODUCT_BUILD_SYSTEM_IMAGE PRODUCT_BUILD_VENDOR_IMAGE PRODUCT_BUILD_PRODUCT_IMAGE PRODUCT_BUILD_SYSTEM_EXT_IMAGE PRODUCT_BUILD_USERDATA_IMAGE PRODUCT_BUILD_VBMETA_IMAGE' > "$root/logs/framework-product-vars.txt"
python3 - <<'PY'
from pathlib import Path
import shlex
values = {}
for line in Path('/srv/android/asus-device-product/logs/framework-product-vars.txt').read_text().splitlines():
    key, sep, value = line.partition('=')
    if sep:
        values[key] = ' '.join(shlex.split(value))
assert values['TARGET_DEVICE'] == 'p00a' and values['TARGET_ARCH'] == 'arm64', values
assert values['PLATFORM_SDK_VERSION'] == '37' and values['PLATFORM_VERSION_LAST_STABLE'] == '17', values
for name in ['BOOT', 'RECOVERY', 'SYSTEM', 'VENDOR', 'PRODUCT', 'SYSTEM_EXT', 'USERDATA', 'VBMETA']:
    assert values[f'PRODUCT_BUILD_{name}_IMAGE'] == 'false', values
PY
m -j8 framework-minus-apex services app_process surfaceflinger
date -u --iso-8601=seconds > "$root/logs/framework-build-complete"
