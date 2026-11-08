#!/bin/bash
set -euo pipefail
R=/srv/android/asus-network-runtime
mkdir -p "$R/tmp"
export TMPDIR="$R/tmp"
args=(-C "$R/kernel" O="$R/build-r1" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ KBUILD_BUILD_USER=asus-port KBUILD_BUILD_HOST=network-runtime KBUILD_BUILD_VERSION=1 'KBUILD_BUILD_TIMESTAMP=Fri Nov 6 00:00:00 UTC 2026')
make "${args[@]}" olddefconfig
make "${args[@]}" -j1 Image
sha256sum "$R/build-r1/.config" "$R/build-r1/arch/arm64/boot/Image"
