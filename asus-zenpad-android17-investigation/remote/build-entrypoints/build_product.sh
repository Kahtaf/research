#!/bin/bash
set -eo pipefail
cd /srv/android/lineage24
source build/envsetup.sh
lunch lineage_p00a-trunk_staging-userdebug
build/soong/soong_ui.bash --dumpvars-mode --vars='TARGET_DEVICE TARGET_ARCH TARGET_KERNEL_SOURCE PRODUCT_SHIPPING_API_LEVEL PRODUCT_BUILD_BOOT_IMAGE PRODUCT_BUILD_RECOVERY_IMAGE PRODUCT_BUILD_SYSTEM_IMAGE PRODUCT_BUILD_VENDOR_IMAGE KERNEL_BUILD_OUT_PREFIX' >/srv/android/asus-device-product/logs/product-vars.txt
python3 - <<'PY'
from pathlib import Path
import shlex,json
p=Path('/srv/android/asus-device-product/logs/product-vars.txt');values={}
for line in p.read_text().splitlines():
    key,sep,value=line.partition('=')
    if sep:
        parts=shlex.split(value);values[key]=' '.join(parts)
assert values['TARGET_DEVICE']=='p00a',values
assert values['TARGET_ARCH']=='arm64',values
assert values['TARGET_KERNEL_SOURCE']=='kernel/asus/p00a',values
assert values['PRODUCT_SHIPPING_API_LEVEL']=='23',values
for key in ['PRODUCT_BUILD_BOOT_IMAGE','PRODUCT_BUILD_RECOVERY_IMAGE','PRODUCT_BUILD_SYSTEM_IMAGE','PRODUCT_BUILD_VENDOR_IMAGE']:
    assert values[key]=='false',(key,values)
Path('/srv/android/asus-device-product/logs/product-vars-verified.json').write_text(json.dumps(values,indent=2)+'\n')
print('Real ASUS kernel settings exported; image generation disabled.')
PY
m -j8 init com.android.adbd
date -u --iso-8601=seconds >/srv/android/asus-device-product/logs/init-adbd-build-complete
