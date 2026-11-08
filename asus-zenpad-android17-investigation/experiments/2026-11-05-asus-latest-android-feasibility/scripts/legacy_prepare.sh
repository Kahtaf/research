#!/bin/sh
set -eu
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq make gcc libc6-dev bc > /audit/evidence/build/legacy-tools-install.log 2>&1
cd /audit/sources/asus-original/kernel-3.18
out=/audit/build/asus-gcc49
mkdir -p "$out"
cp arch/arm64/configs/asus8163_tb_380_m_defconfig "$out/.config"
export ARCH=arm64
export CROSS_COMPILE=/audit/sources/asus-original/prebuilts/gcc/linux-x86/aarch64/aarch64-linux-android-4.9/bin/aarch64-linux-android-
make O="$out" ROOTDIR=/audit/sources/asus-original olddefconfig > /audit/evidence/build/gcc49-olddefconfig.log 2>&1
set +e
make O="$out" ROOTDIR=/audit/sources/asus-original -j4 prepare > /audit/evidence/build/gcc49-prepare.log 2>&1
result=$?
printf '%s\n' "$result" > /audit/evidence/build/gcc49-prepare-exit.txt
cat /audit/evidence/build/gcc49-prepare.log
exit "$result"
