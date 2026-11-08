#!/bin/bash
set -euo pipefail
root=/srv/android/asus-android17
base=$root/kernel-network
source=$root/kernel-bpf-ids
test "$(git -C "$base" rev-parse HEAD)" = de61780979adc3c52068e244aa62ae0369c00527
test -z "$(git -C "$base" status --porcelain)"
test ! -e "$source"
test ! -e "$root/build-bpf-ids"
python3 - <<'PY'
import json
from pathlib import Path
p=Path('/srv/android/asus-virtual-validation/ids/logs/qemu-result.json')
r=json.loads(p.read_text())
assert r['source']['revision']=='34a8afba47785b0ff9dc2a72dade73c945a54a55'
assert r['ids']['all_checks_passed'] and r['basic_bpf_passed']
assert r['qemu_returncode']==0 and not r['timed_out']
PY
git -C "$base" worktree add -b asus-bpf-ids-hardware "$source" HEAD
git -C "$source" am /srv/android/asus-virtual-validation/ids/bpf-ids.patch
git -C "$source" diff --check HEAD~1 HEAD
git -C "$source" rev-parse HEAD > "$root/logs/bpf-ids-hardware-source.txt"
mkdir "$root/build-bpf-ids"
cp "$root/build-network/.config" "$root/build-bpf-ids/.config"
args=( -C "$source" O="$root/build-bpf-ids" ARCH=arm64
  CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++
  KBUILD_BUILD_USER=asus-port KBUILD_BUILD_HOST=offline-builder
  KBUILD_BUILD_VERSION=1 'KBUILD_BUILD_TIMESTAMP=Fri Nov 6 00:00:00 UTC 2026' )
make "${args[@]}" olddefconfig > "$root/logs/bpf-ids-hardware-config.log" 2>&1
make "${args[@]}" -j12 Image.gz-dtb > "$root/logs/bpf-ids-hardware-build.log" 2>&1
printf '%s  %s\n' \
  577a1ca5fbfe646ca02a50c190ac60efab0edd73c77c904a33865859e2d87bfc \
  "$root/build-bpf-ids/arch/arm64/boot/dts/mediatek/asus-p00a.dtb" | sha256sum -c -
sha256sum "$root/build-bpf-ids/arch/arm64/boot/Image.gz-dtb" \
  "$root/build-bpf-ids/arch/arm64/boot/dts/mediatek/asus-p00a.dtb" \
  "$root/build-bpf-ids/.config" > "$root/logs/bpf-ids-hardware-artifact-hashes.txt"
date -u --iso-8601=seconds > "$root/logs/bpf-ids-hardware-build-complete"
