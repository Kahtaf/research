#!/bin/bash
set -euo pipefail
cd /srv/android
mkdir -p asus-hardware/downloads asus-hardware/sources asus-hardware/logs asus-hardware/build
cd asus-hardware
archive=downloads/mt8163-dc63af1.tar.gz
if [ ! -f "$archive" ]; then
  curl -fL --retry 3 https://codeload.github.com/amazon-oss/android_kernel_amazon_mt8163/tar.gz/dc63af1741072236efb511499f1f0b9dd281d694 -o "$archive"
fi
echo 'b64ccd9545967628d4cb4b280ef11863cf04aebd414eac47fd9062a73283de91  downloads/mt8163-dc63af1.tar.gz' | sha256sum -c -
if [ ! -d sources/kernel ]; then
  mkdir sources/kernel
  tar -xzf "$archive" -C sources/kernel --strip-components=1
  for p in patches/*.patch; do
    patch --batch --forward -p1 -d sources/kernel <"$p"
  done
fi
# Keep source and output on this VM's case-sensitive ext4 filesystem.
build_args=( -C sources/kernel O=/srv/android/asus-hardware/build ARCH=arm64
  CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++
  KBUILD_BUILD_USER=asus-port KBUILD_BUILD_HOST=offline-builder
  KBUILD_BUILD_VERSION=1 'KBUILD_BUILD_TIMESTAMP=Thu Nov 5 00:00:00 UTC 2026' )
make "${build_args[@]}" asus_p00a_defconfig >logs/defconfig.log 2>&1
make "${build_args[@]}" -j12 Image.gz-dtb >logs/build.log 2>&1
sha256sum build/arch/arm64/boot/Image.gz-dtb build/arch/arm64/boot/dts/mediatek/asus-p00a.dtb build/.config >logs/artifact-hashes.txt
date -u --iso-8601=seconds >logs/build-complete
