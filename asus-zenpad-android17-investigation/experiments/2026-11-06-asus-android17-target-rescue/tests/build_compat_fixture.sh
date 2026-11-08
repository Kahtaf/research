#!/bin/bash
set -euo pipefail
R=/srv/android/asus-target-rescue
export TMPDIR=$R/build
test ! -e "$R/build/compat-kernel"
# Independent, completed runtime fixture only. Never read or write the active physical kernel.
cp -a --reflink=auto /srv/android/asus-android17-runtime-prereqs/kernel "$R/build/compat-kernel"
cp -a --reflink=auto /srv/android/asus-android17-runtime-prereqs/build-r4 "$R/build/compat-out"
K=$R/build/compat-kernel
B=$R/build/compat-out
"$K/scripts/config" --file "$B/.config" -e COMPAT
"$K/scripts/config" --file "$B/.config" --set-val ARCH_MMAP_RND_COMPAT_BITS 16
args=(-C "$K" O="$B" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ KBUILD_BUILD_USER=asus-port KBUILD_BUILD_HOST=target-rescue-fixture KBUILD_BUILD_VERSION=1 'KBUILD_BUILD_TIMESTAMP=Fri Nov 6 00:00:00 UTC 2026')
make "${args[@]}" olddefconfig
"$K/scripts/diffconfig" /srv/android/asus-android17-runtime-prereqs/handoff-r1/artifacts/kernel-runtime-r4.config "$B/.config" > "$R/evidence/compat-kernel-config-delta.txt"
make "${args[@]}" -j2 Image
sha256sum "$B/.config" "$B/arch/arm64/boot/Image" > "$R/evidence/compat-kernel.sha256"
