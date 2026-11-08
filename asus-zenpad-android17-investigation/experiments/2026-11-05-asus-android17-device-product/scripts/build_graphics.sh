#!/bin/bash
set -eo pipefail
root=/srv/android/asus-device-product
revision=${1:?numbered revision required}
[[ "$revision" =~ ^r[0-9]+$ ]] || exit 2
cd /srv/android/lineage24
source build/envsetup.sh
lunch lineage_p00a-trunk_staging-userdebug
# Build the entire bounded closure; the strict Soong ELF checks are mandatory.
mapfile -t blobs < <(sed -n 's/^    name: "\(p00a_legacy_[^"]*\)",/\1/p' vendor/asus/p00a/Android.bp)
m -j8 android.hardware.graphics.composer@2.1-service android.hardware.graphics.allocator@2.0-service android.hardware.graphics.allocator@2.0-impl android.hardware.graphics.mapper@2.0-impl libp00a_legacy_memory linkerconfig linkerconfig_contents_fulltest "${blobs[@]}"
out/host/linux-x86/nativetest64/linkerconfig_contents_fulltest/linkerconfig_contents_fulltest
python3 "$(dirname "${BASH_SOURCE[0]}")/capture_graphics_revision.py" --revision "$revision"
date -u --iso-8601=seconds > "$root/logs/graphics-build-$revision-complete"
