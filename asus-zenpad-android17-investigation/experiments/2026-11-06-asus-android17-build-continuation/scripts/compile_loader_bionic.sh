#!/bin/bash
set -euo pipefail
R=/srv/android/asus-build-continuation
A=/srv/android/lineage24
C=$A/prebuilts/clang/host/linux-x86/clang-r596125/bin
S=$A/out/soong/ndk/sysroot
O=$R/loader-bionic-arm64-r1
mkdir "$O"
exec > "$O/build.log" 2>&1
trap 'echo $? > "$O/exit-code"' EXIT
"$C/clang" --version
flags=(--target=aarch64-linux-android23 --sysroot="$S" -isystem "$S/usr/include/aarch64-linux-android" -O2 -fPIE -Wall -Wextra -Werror -std=c11)
for name in p00a_wmt wmt_protocol bt_record; do
    "$C/clang" "${flags[@]}" -E "$R/product-device/radio/src/$name.c" -o "$O/$name.i"
    "$C/clang" "${flags[@]}" -E "$R/product-device/radio/src/$name.c" -o "$O/$name-repeat.i"
    cmp "$O/$name.i" "$O/$name-repeat.i"
    "$C/clang" --target=aarch64-linux-android23 -O2 -fPIE -Wall -Wextra -Werror -std=c11 -c "$O/$name.i" -o "$O/$name.o"
done
cp "$S/usr/lib/aarch64-linux-android/23/libc.so" "$O/libc.so"
for name in crtbegin_dynamic crtend_android; do
    cp "$A/out/soong/.intermediates/bionic/libc/$name/android_vendor_arm64_armv8-a/$name.o" "$O/$name.o"
done
"$C/clang" --target=aarch64-linux-android23 -fuse-ld=lld -nostdlib -pie -Wl,--no-undefined,-z,noexecstack,-z,relro,-z,now,-dynamic-linker,/system/bin/linker64 "$O/crtbegin_dynamic.o" "$O/p00a_wmt.o" "$O/wmt_protocol.o" "$O/bt_record.o" -L"$O" -lc "$O/crtend_android.o" -o "$O/p00a-wmt"
"$C/llvm-readelf" -h -l -d -s "$O/p00a-wmt" > "$O/elf.txt"
sha256sum "$O/"*.i "$O/"*.o "$O/p00a-wmt" "$O/libc.so" "$R/product-device/radio/src/"*.c > "$O/sha256"
