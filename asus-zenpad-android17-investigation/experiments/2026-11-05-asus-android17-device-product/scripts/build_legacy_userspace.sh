#!/bin/bash
set -eo pipefail
python3 /srv/android/asus-device-product/capture_framework_checkpoint.py
cd /srv/android/lineage24
source build/envsetup.sh
lunch lineage_p00a-trunk_staging-userdebug
m -j8 init_first_stage linker toybox sh linkerconfig netbpfload netd services service-connectivity surfaceflinger android.hardware.lights-service.asus-p00a libp00a_legacy_memory libutilscallstack
date -u --iso-8601=seconds > /srv/android/asus-device-product/logs/legacy-core-build-complete
python3 /srv/android/asus-device-product/deploy_vendor_graphics.py
m -j8 android.hardware.graphics.composer@2.1-service android.hardware.graphics.allocator@2.0-service android.hardware.graphics.allocator@2.0-impl android.hardware.graphics.mapper@2.0-impl p00a_legacy_libGLES_mali p00a_legacy_gralloc_mt8163
python3 /srv/android/asus-device-product/capture_platform_symbols.py
