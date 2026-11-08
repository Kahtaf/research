#!/bin/sh
set -eu
src=/work/sources/kernel
out=/work/artifacts
mkdir -p "$out"
aarch64-linux-gnu-cpp -nostdinc -undef -D__DTS__ -x assembler-with-cpp -I"$src/include" -I"$src/arch/arm64/boot/dts/mediatek" "$src/arch/arm64/boot/dts/mediatek/asus-p00a.dts" -o "$out/asus-p00a.preprocessed.dts"
dtc -i "$src/arch/arm64/boot/dts/mediatek" -I dts -O dtb -o "$out/asus-p00a-COMPILE-ONLY.dtb" "$out/asus-p00a.preprocessed.dts"
