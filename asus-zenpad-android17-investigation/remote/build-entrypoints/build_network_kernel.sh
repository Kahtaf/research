#!/bin/bash
set -euo pipefail
root=/srv/android/asus-android17
build_args=( -C "$root/kernel-network" O="$root/build-network" ARCH=arm64
  CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++
  KBUILD_BUILD_USER=asus-port KBUILD_BUILD_HOST=offline-builder
  KBUILD_BUILD_VERSION=1 'KBUILD_BUILD_TIMESTAMP=Fri Nov 6 00:00:00 UTC 2026' )
make "${build_args[@]}" olddefconfig > "$root/logs/network-kernel-config.log" 2>&1
for feature in BPF_JIT NET_CLS_BPF NET_CLS_MATCHALL NET_ACT_BPF EROFS_FS; do
  grep -qx "CONFIG_${feature}=y" "$root/build-network/.config"
done
make "${build_args[@]}" -j6 Image.gz-dtb > "$root/logs/network-kernel-build.log" 2>&1
sha256sum "$root/build-network/arch/arm64/boot/Image.gz-dtb" \
  "$root/build-network/arch/arm64/boot/dts/mediatek/asus-p00a.dtb" \
  "$root/build-network/.config" > "$root/logs/network-kernel-artifact-hashes.txt"
date -u --iso-8601=seconds > "$root/logs/network-kernel-build-complete"
