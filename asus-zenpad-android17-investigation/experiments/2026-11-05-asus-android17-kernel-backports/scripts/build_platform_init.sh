#!/bin/bash
# Compiler/platform check only. mini_arm64 is not an ASUS product.
set -eo pipefail
cd /srv/android/lineage24
source build/envsetup.sh
lunch mini_arm64-trunk_staging-userdebug
m -j8 init adbd
date -u --iso-8601=seconds >/srv/android/logs/platform-init-build-complete
