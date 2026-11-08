#!/bin/bash
set -euo pipefail
R=/srv/android/asus-build-continuation
K=$R/kernel
rev=${1:?revision}; [[ "$rev" =~ ^r[0-9]+$ ]]
record=$R/logs/kernel-$rev
exec 9>"$R/logs/kernel.lock"; flock -n 9
[[ ! -e "$record.started" ]]
date -u --iso-8601=seconds > "$record.started"
finish() { result=$?; trap - EXIT; echo "$result" > "$record.exit-code"; date -u --iso-8601=seconds > "$record.finished"; exit "$result"; }; trap finish EXIT
out=$R/build
if [[ ! -e "$out" ]]; then mkdir "$out"; cp "$R/inputs/soc.config" "$out/.config"; fi
for opt in ASUS_P00A_RADIO MTK_COMBO MTK_COMBO_CHIP_CONSYS_8163 MTK_COMBO_BT MTK_COMBO_WIFI MTK_BTIF CFG80211 PM PM_GENERIC_DOMAINS RESET_CONTROLLER MTK_EMI_MPU PM_WAKELOCKS REGULATOR_MT6323; do "$K/scripts/config" --file "$out/.config" --enable "$opt"; done
make -C "$K" O="$out" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ olddefconfig
cp "$out/.config" "$record.config"
aarch64-linux-gnu-gcc --version
make -C "$K" O="$out" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ -j4 Image.gz-dtb
sha256sum "$out/arch/arm64/boot/Image.gz-dtb" "$out/.config" > "$record.sha256"
date -u --iso-8601=seconds > "$record.complete"
