#!/bin/bash
set -euo pipefail
R=/srv/android/asus-android17-runtime-prereqs
export TMPDIR=$R/tmp
k=$R/kernel
b=$R/build-r2
test ! -e "$b"
cp -a "$R/build-r1" "$b"
for opt in MISC_FILESYSTEMS EROFS_FS EROFS_FS_XATTR EROFS_FS_POSIX_ACL EROFS_FS_SECURITY EROFS_FS_ZIP EROFS_FS_ARMV8_ACCELERATED_LZ4 AUDIT SECURITY_SELINUX SECURITY_SELINUX_BOOTPARAM SECURITY_SELINUX_DEVELOP SECURITY_SELINUX_AVC_STATS DEFAULT_SECURITY_SELINUX; do
 "$k/scripts/config" --file "$b/.config" -e "$opt"
done
"$k/scripts/config" --file "$b/.config" --set-val SECURITY_SELINUX_CHECKREQPROT_VALUE 0
args=(-C "$k" O="$b" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ KBUILD_BUILD_USER=asus-port KBUILD_BUILD_HOST=runtime-prereqs KBUILD_BUILD_VERSION=1 'KBUILD_BUILD_TIMESTAMP=Fri Nov 6 00:00:00 UTC 2026')
make "${args[@]}" olddefconfig
"$k/scripts/diffconfig" "$R/build-r1/.config" "$b/.config" > "$R/evidence/config-delta-r2.txt"
python3 "$R/source/check_kernel_config.py" "$b/.config"
make "${args[@]}" -j2 Image
sha256sum "$b/.config" "$b/arch/arm64/boot/Image" > "$R/evidence/kernel-r2.sha256"
