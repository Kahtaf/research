#!/bin/bash
set -euo pipefail
cd /srv/android/asus-android17
mkdir -p logs build-erofs
# Keep source and output on this VM's case-sensitive ext4 filesystem.
build_args=( -C /srv/android/asus-android17/kernel O=/srv/android/asus-android17/build-erofs ARCH=arm64
  CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++
  KBUILD_BUILD_USER=asus-port KBUILD_BUILD_HOST=offline-builder
  KBUILD_BUILD_VERSION=1 'KBUILD_BUILD_TIMESTAMP=Thu Nov 5 00:00:00 UTC 2026' )
if [ "${1:-}" != --resume ]; then
make "${build_args[@]}" asus_p00a_defconfig >/srv/android/asus-android17/logs/erofs-defconfig.log 2>&1
/srv/android/asus-android17/kernel/scripts/config --file /srv/android/asus-android17/build-erofs/.config -e EROFS_FS
make "${build_args[@]}" olddefconfig >>/srv/android/asus-android17/logs/erofs-defconfig.log 2>&1
fi
make "${build_args[@]}" -j12 Image.gz-dtb >/srv/android/asus-android17/logs/erofs-build.log 2>&1
sha256sum /srv/android/asus-android17/build-erofs/arch/arm64/boot/Image.gz-dtb /srv/android/asus-android17/build-erofs/arch/arm64/boot/dts/mediatek/asus-p00a.dtb /srv/android/asus-android17/build-erofs/.config >/srv/android/asus-android17/logs/erofs-artifact-hashes.txt
date -u --iso-8601=seconds >/srv/android/asus-android17/logs/erofs-build-complete
