#!/bin/bash
set -eo pipefail
[[ "$PWD" == /srv/android/lineage24 ]]
[[ "${SERVICE_BUILD_LOCK_FD:-}" =~ ^[0-9]+$ ]]
unset WITH_ADB_INSECURE SELINUX_IGNORE_NEVERALLOWS SOONG_ALLOW_MISSING_DEPENDENCIES ALLOW_MISSING_DEPENDENCIES
source build/envsetup.sh
lunch lineage_p00a-trunk_staging-userdebug
m -j8 apexd hwservicemanager keystore2 servicemanager android.hardware.keymaster@4.0-service lmkd com.android.adbd
