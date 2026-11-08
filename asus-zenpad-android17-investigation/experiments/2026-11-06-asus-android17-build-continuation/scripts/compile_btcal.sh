#!/bin/bash
set -euo pipefail
R=/srv/android/asus-build-continuation
A=/srv/android/lineage24
C=$A/prebuilts/clang/host/linux-x86/clang-r596125/bin/clang
S=$A/out/soong/ndk/sysroot
O=$R/btcal-arm32-r3
mkdir "$O"
exec > "$O/build.log" 2>&1
trap 'echo $? > "$O/exit-code"' EXIT
"$C" --version
flags=(--target=armv7a-linux-androideabi23 --sysroot="$S" -isystem "$S/usr/include/arm-linux-androideabi" -O2 -fPIC -Wall -Wextra -Werror -std=c11)
"$C" "${flags[@]}" -E "$R/product-device/radio/src/bt_record.c" -o "$O/bt_record.i"
"$C" "${flags[@]}" -E "$R/product-device/radio/src/bt_record.c" -o "$O/bt_record-repeat.i"
cmp "$O/bt_record.i" "$O/bt_record-repeat.i"
"$C" --target=armv7a-linux-androideabi23 -O2 -fPIC -Wall -Wextra -Werror -std=c11 -c "$O/bt_record.i" -o "$O/bt_record.o"
cp "$S/usr/lib/arm-linux-androideabi/23/libc.so" "$O/libc.so"
"$C" --target=armv7a-linux-androideabi23 -fuse-ld=lld -nostdlib -shared -Wl,--no-undefined,-soname,libbtcal.so "$O/bt_record.o" -L"$O" -lc -o "$O/libbtcal.so"
"$A/prebuilts/clang/host/linux-x86/clang-r596125/bin/llvm-readelf" -h -d -s "$O/libbtcal.so" > "$O/elf.txt"
sha256sum "$O/bt_record.i" "$O/bt_record.o" "$O/libbtcal.so" "$O/libc.so" "$R/product-device/radio/src/bt_record.c" > "$O/sha256"
