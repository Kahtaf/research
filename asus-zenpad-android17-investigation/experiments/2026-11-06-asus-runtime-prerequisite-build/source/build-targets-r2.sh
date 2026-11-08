#!/bin/bash
set -eo pipefail
[[ "$PWD" == /srv/android/lineage24 ]]
[[ "${SERVICE_BUILD_LOCK_FD:-}" =~ ^[0-9]+$ ]]
unset WITH_ADB_INSECURE SELINUX_IGNORE_NEVERALLOWS SOONG_ALLOW_MISSING_DEPENDENCIES ALLOW_MISSING_DEPENDENCIES
export NINJA_ARGS="-v"
source build/envsetup.sh
lunch lineage_p00a-trunk_staging-userdebug
m -j8 \
  out/target/product/p00a/system/bin/boringssl_self_test32 \
  out/target/product/p00a/system/bin/boringssl_self_test64 \
  out/target/product/p00a/system/apex/com.android.runtime.apex \
  out/target/product/p00a/system/build.prop \
  out/target/product/p00a/system/system_ext/build.prop \
  out/target/product/p00a/system/product/build.prop \
  out/target/product/p00a/obj/PACKAGING/apexkeys_intermediates/apexkeys.txt
