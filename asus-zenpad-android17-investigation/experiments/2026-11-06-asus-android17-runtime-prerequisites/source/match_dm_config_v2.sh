#!/bin/bash
set -euo pipefail
R=/srv/android/asus-android17-runtime-prereqs
export TMPDIR=$R/tmp
k=$R/kernel
b=$R/build-r4
test ! -e "$b"
cp -a "$R/build-r3" "$b"
for opt in DM_ANDROID_VERITY_AT_MOST_ONCE_DEFAULT_ENABLED DM_CRYPT DM_UEVENT CRYPTO_LZ4; do
 "$k/scripts/config" --file "$b/.config" -e "$opt"
done
args=(-C "$k" O="$b" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ KBUILD_BUILD_USER=asus-port KBUILD_BUILD_HOST=runtime-prereqs KBUILD_BUILD_VERSION=1 'KBUILD_BUILD_TIMESTAMP=Fri Nov 6 00:00:00 UTC 2026')
make "${args[@]}" olddefconfig
"$k/scripts/diffconfig" "$R/build-r2/.config" "$b/.config" > "$R/evidence/config-delta-r4.txt"
python3 "$R/source/check_expanded_config.py" "$b/.config"
make "${args[@]}" -j2 Image
sha256sum "$b/.config" "$b/arch/arm64/boot/Image" > "$R/evidence/kernel-r4.sha256"
