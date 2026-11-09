#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Derivative of kaantcp/z380m-alpine src/touchbridge/build.sh.
# Copyright (C) 2026 kaantcp (https://github.com/kaantcp)
# Change: build a local source copy with mandatory kernel-reported axis ranges.
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SPIKE=$(CDPATH= cd -- "$HERE/../.." && pwd)
OUT=${1:-$SPIKE/artifacts/goodix}
mkdir -p "$OUT"
cp "$SPIKE/sources/z380m-alpine/src/touchbridge/z380m-touchbridge.c" "$OUT/z380m-touchbridge.c"
patch -d "$OUT" -p1 < "$HERE/touchbridge-no-fallback.patch"
exec "${CC:-clang}" --target=aarch64-linux-gnu -Wall -Wextra -Os \
  -ffreestanding -fno-builtin -fno-stack-protector -fno-pic -fno-pie \
  -fno-asynchronous-unwind-tables -fno-unwind-tables \
  -nostdlib -static -fuse-ld=lld \
  -Wl,-e,_start -Wl,--build-id=none -Wl,-z,max-page-size=4096 -Wl,-z,norelro -Wl,-z,noseparate-code \
  -Wl,--gc-sections -Wl,-s \
  -o "$OUT/z380m-touchbridge.arm64" "$OUT/z380m-touchbridge.c"
