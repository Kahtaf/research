#!/bin/bash
set -euo pipefail
root=/srv/android/asus-userspace-startup
source=/srv/android/asus-virtual-validation/kernel-fd
test "$(git -C "$source" rev-parse HEAD)" = fcb1b6c2de6348e2724981dcd520dec631ed5255
test -z "$(git -C "$source" status --porcelain)"
test ! -e "$root/kernel-build"
mkdir "$root/kernel-build"
cp /srv/android/asus-virtual-validation/fd/build/.config "$root/kernel-build/.config"
"$source/scripts/config" --file "$root/kernel-build/.config" -e ADVISE_SYSCALLS
args=(-C "$source" O="$root/kernel-build" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
      HOSTCC=gcc HOSTCXX=g++ KBUILD_BUILD_USER=asus-port KBUILD_BUILD_HOST=userspace-startup
      KBUILD_BUILD_VERSION=1 'KBUILD_BUILD_TIMESTAMP=Fri Nov 6 00:00:00 UTC 2026')
make "${args[@]}" olddefconfig
"$source/scripts/diffconfig" -m /srv/android/asus-virtual-validation/fd/build/.config "$root/kernel-build/.config" > "$root/kernel-config-delta.txt"
make "${args[@]}" -j6 Image
date -u --iso-8601=seconds > "$root/kernel-build-complete"
