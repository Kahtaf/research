#!/bin/bash
set -eo pipefail
rev=${1:?unique rN}
[[ "$rev" =~ ^r[0-9]+$ ]]
k=/srv/android/asus-android17/kernel-bpf-fd
out=${KERNEL_OUT:-/srv/android/asus-android17/build-main-battery-soc-$rev}
record=/srv/android/asus-build-integration/logs/kernel-$rev
test ! -e "$record.started"
if [[ -e "$out" ]]; then test -n "$KERNEL_OUT"; fi
date -u --iso-8601=seconds > "$record.started"
finish() { result=$?; trap - EXIT; echo "$result" > "$record.exit-code"; date -u --iso-8601=seconds > "$record.finished"; exit "$result"; }
trap finish EXIT
if [[ ! -e "$out" ]]; then
 mkdir "$out"
 cp /srv/android/asus-android17/build-bpf-fd/.config "$out/.config"
fi
"$k/scripts/config" --file "$out/.config" --enable ASUS_P00A_BATTERY_DIAGNOSTIC --disable MTK_MULTI_BAT_PROFILE_SUPPORT --disable MTK_BATTERY_LIFETIME_DATA_SUPPORT --enable ASUS_P00A_MAIN_BATTERY_SOC
make -C "$k" O="$out" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ olddefconfig
grep -E 'CONFIG_(ASUS_P00A|MTK_MULTI_BAT_PROFILE_SUPPORT|MTK_BATTERY_LIFETIME_DATA_SUPPORT|MTK_SMART_BATTERY|MTK_PMIC|OF=)' "$out/.config" | tee "$record.config-flags"
aarch64-linux-gnu-gcc --version
make -C "$k" O="$out" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ -j8 Image.gz-dtb
sha256sum "$out/arch/arm64/boot/Image.gz-dtb" "$out/arch/arm64/boot/Image.gz" "$out/.config" > "$record.sha256"
date -u --iso-8601=seconds > "$record.complete"
