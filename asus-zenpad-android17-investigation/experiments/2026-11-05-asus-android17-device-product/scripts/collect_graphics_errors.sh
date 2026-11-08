#!/bin/bash
set -eo pipefail
cd /srv/android/lineage24
source build/envsetup.sh
lunch lineage_p00a-trunk_staging-userdebug
m -j8 -k0 android.hardware.graphics.composer@2.1-service android.hardware.graphics.allocator@2.0-service android.hardware.graphics.allocator@2.0-impl android.hardware.graphics.mapper@2.0-impl p00a_legacy_libGLES_mali p00a_legacy_gralloc_mt8163
