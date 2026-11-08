#!/bin/bash
set -euo pipefail
base=/srv/android/asus-virtual-validation
candidate=${1:-baseline}
case "$candidate" in
  baseline) root=$base; source=$base/kernel; extra_cflags=() ;;
  ids) root=$base/ids; source=$base/kernel-ids; extra_cflags=(-DEXPECT_BPF_IDS) ;;
  fd) root=$base/fd; source=$base/kernel-fd; extra_cflags=(-DEXPECT_BPF_IDS -DEXPECT_BPF_FD) ;;
  meta) root=$base/meta; source=$base/kernel-meta; extra_cflags=(-DEXPECT_BPF_IDS -DEXPECT_BPF_FD -DEXPECT_BPF_META) ;;
  *) exit 2 ;;
esac
expected=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["revision"])' "$root/source-provenance.json")
test "$(git -C "$source" rev-parse HEAD)" = "$expected"
test -z "$(git -C "$source" status --porcelain)"
mkdir -p "$root/logs" "$root/build"
args=( -C "$source" O="$root/build" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
  HOSTCC=gcc HOSTCXX=g++ KBUILD_BUILD_USER=asus-port KBUILD_BUILD_HOST=virtual-test
  KBUILD_BUILD_VERSION=1 'KBUILD_BUILD_TIMESTAMP=Fri Nov 6 00:00:00 UTC 2026' )
make "${args[@]}" allnoconfig > "$root/logs/config.log" 2>&1
for option in SMP HOTPLUG_CPU ARCH_VEXPRESS ARM_AMBA ARM_GIC ARM_GIC_V3 ARM_ARCH_TIMER \
  ARM_PSCI_FW TTY SERIAL_AMBA_PL011 SERIAL_AMBA_PL011_CONSOLE PRINTK \
  DEVTMPFS DEVTMPFS_MOUNT PROC_FS SYSFS BINFMT_ELF BLK_DEV_INITRD RD_GZIP \
  FUTEX EPOLL SIGNALFD TIMERFD EVENTFD NET INET UNIX BPF_SYSCALL \
  BPF_JIT MODULES CGROUPS CGROUP_BPF; do
  "$source/scripts/config" --file "$root/build/.config" -e "$option"
done
if [ "$candidate" != baseline ]; then
  "$source/scripts/config" --file "$root/build/.config" -e MULTIUSER
fi
"$source/scripts/config" --file "$root/build/.config" --set-val NR_CPUS 4
make "${args[@]}" olddefconfig >> "$root/logs/config.log" 2>&1
make "${args[@]}" -j10 Image > "$root/logs/build.log" 2>&1
aarch64-linux-gnu-gcc -static -O2 -Wall -Wextra -Werror "${extra_cflags[@]}" \
  "$root/bpf_smoke_init.c" -o "$root/init"
python3 "$root/make_initramfs.py" "$root"
sha256sum "$root/build/arch/arm64/boot/Image" "$root/build/.config" \
  "$root/init" "$root/initramfs.cpio.gz" > "$root/logs/artifact-hashes.txt"
date -u --iso-8601=seconds > "$root/logs/build-complete"
