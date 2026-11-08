#!/bin/bash
set -euo pipefail
root=/srv/android/asus-android17
base=$root/kernel-bpf-ids
source=$root/kernel-bpf-fd
test "$(git -C "$base" rev-parse HEAD)" = 790faa7607c819a5d61425283cb4784bc413b735
test -z "$(git -C "$base" status --porcelain)"
test ! -e "$source"
test ! -e "$root/build-bpf-fd"
python3 - <<'PY'
import json
from pathlib import Path
r=json.loads(Path('/srv/android/asus-virtual-validation/fd/logs/qemu-result.json').read_text())
assert r['source']['revision']=='fcb1b6c2de6348e2724981dcd520dec631ed5255'
assert r['ids']['all_checks_passed'] and r['basic_bpf_passed']
assert r['fd_checks']['all_checks_passed'] and r['fd_checks']['prog_array_userref']
assert r['fd_checks']['map_race_hits']>0 and r['fd_checks']['program_race_hits']>0
assert r['qemu_returncode']==0 and not r['timed_out']
PY
git -C "$base" worktree add -b asus-bpf-fd-hardware "$source" HEAD
git -C "$source" am /srv/android/asus-virtual-validation/fd/bpf-fd.patch
git -C "$source" diff --check HEAD~2 HEAD
git -C "$source" rev-parse HEAD > "$root/logs/bpf-fd-hardware-source.txt"
mkdir "$root/build-bpf-fd"
cp "$root/build-bpf-ids/.config" "$root/build-bpf-fd/.config"
args=( -C "$source" O="$root/build-bpf-fd" ARCH=arm64
  CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++
  KBUILD_BUILD_USER=asus-port KBUILD_BUILD_HOST=offline-builder
  KBUILD_BUILD_VERSION=1 'KBUILD_BUILD_TIMESTAMP=Fri Nov 6 00:00:00 UTC 2026' )
make "${args[@]}" olddefconfig > "$root/logs/bpf-fd-hardware-config.log" 2>&1
make "${args[@]}" -j8 Image.gz-dtb > "$root/logs/bpf-fd-hardware-build.log" 2>&1
printf '%s  %s\n' \
  577a1ca5fbfe646ca02a50c190ac60efab0edd73c77c904a33865859e2d87bfc \
  "$root/build-bpf-fd/arch/arm64/boot/dts/mediatek/asus-p00a.dtb" | sha256sum -c -
sha256sum "$root/build-bpf-fd/arch/arm64/boot/Image.gz-dtb" \
  "$root/build-bpf-fd/arch/arm64/boot/dts/mediatek/asus-p00a.dtb" \
  "$root/build-bpf-fd/.config" > "$root/logs/bpf-fd-hardware-artifact-hashes.txt"
date -u --iso-8601=seconds > "$root/logs/bpf-fd-hardware-build-complete"
