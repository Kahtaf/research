#!/bin/sh
set -eu
SPIKE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
mkdir -p "$SPIKE/qa"
clang --version > "$SPIKE/qa/clang-version.txt"
clang -target aarch64-none-elf -c -I "$SPIKE/source/arch/arm64/kernel" \
  "$SPIKE/qa/unit.S" -o "$SPIKE/qa/unit.o" 2> "$SPIKE/qa/assembly.stderr"
"$SPIKE/../2026-11-06-asus-selected-camera-metadata/fixture/venv/bin/python" -B \
  "$SPIKE/scripts/check.py" > "$SPIKE/qa/check.stdout" 2> "$SPIKE/qa/check.stderr"
