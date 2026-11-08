#!/bin/bash
set -eo pipefail
cd /srv/android/lineage24
# lineage_generator exports a file dependency rather than an m module alias.
# Use the already validated ASUS product's generated aggregate Ninja graph.
test -f out/combined-lineage_p00a.ninja
prebuilts/build-tools/linux-x86/bin/ninja -f out/combined-lineage_p00a.ninja -j8 \
  out/soong/.intermediates/vendor/lineage/build/soong/generated_kernel_includes/gen/.dummy_dep
date -u --iso-8601=seconds >/srv/android/asus-device-product/logs/kernel-header-build-complete
