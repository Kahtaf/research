#!/bin/bash
set -euo pipefail
R=/srv/android/asus-android17-runtime-prereqs
k=$R/kernel
b=$R/build-r1
for opt in BLOCK BLK_DEV BLK_DEV_LOOP MD BLK_DEV_DM DM_VERITY DM_VERITY_FEC EXT4_FS EXT4_FS_SECURITY EROFS_FS EROFS_FS_XATTR EROFS_FS_POSIX_ACL EROFS_FS_SECURITY EROFS_FS_ZIP EROFS_FS_ARMV8_ACCELERATED_LZ4 ANDROID ANDROID_BINDER_IPC VIRTIO VIRTIO_MMIO VIRTIO_BLK SECURITY SECURITY_NETWORK SECURITY_SELINUX CRYPTO CRYPTO_SHA256 TMPFS SHMEM; do
 "$k/scripts/config" --file "$b/.config" -e "$opt"
done
"$k/scripts/config" --file "$b/.config" --set-str ANDROID_BINDER_DEVICES binder,hwbinder,vndbinder
args=(-C "$k" O="$b" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ KBUILD_BUILD_USER=asus-port KBUILD_BUILD_HOST=runtime-prereqs KBUILD_BUILD_VERSION=1 'KBUILD_BUILD_TIMESTAMP=Fri Nov 6 00:00:00 UTC 2026')
make "${args[@]}" olddefconfig
"$k/scripts/diffconfig" "$R/inputs/startup.config" "$b/.config" > "$R/evidence/config-delta-r1.txt"
make "${args[@]}" -j2 Image
sha256sum "$b/.config" "$b/arch/arm64/boot/Image" > "$R/evidence/kernel-r1.sha256"
