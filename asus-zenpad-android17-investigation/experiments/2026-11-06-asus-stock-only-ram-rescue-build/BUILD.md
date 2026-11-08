# Offline construction and verification

This document contains no live execute or deployment procedure. Candidate status is STOCK-ONLY/UNAPPROVED with two actual manifest roles; public host approval and timing qualification remain false.

Owned builder fixture: `/srv/android/2026-11-06-asus-stock-only-ram-rescue-build`. Its source, build logs, binaries and reproduction subdirectory already exist. `scripts/remote.py` refuses an existing fixture. Do not rerun creation/build over completed outputs. `assemble_final.py` and `tests/reproduce.py` also refuse existing output directories. Independent reproduction requires a separately owned prefix and review of the fixed path assertions; it must not modify this delivery or its original inputs.

Recorded sequence in `scripts/build_remote.py`: compile daemon; compile policy builder and exact policy/contexts; assemble compressed core with exact original two-role manifest; regenerate core binding; compile static ARM64 helper twice; assemble canonical helper archive/image/padded p10 and external host binding; compile/run core/session/legacy fixtures; run corrected host protocol/durability/contract regressions; run actual-manifest admission and additional core/handoff cases; run binary policy checks; run actual ARM64 extraction probe; reproduce complete image in `artifacts/reproduction`; independently verify image/container. `scripts/postflight.py` checks preserved inputs, unchanged production target code, exact host, generated bindings, layout and toolchain pins.

Compiler flags and every command/output are in `evidence/build-log.json`. Production ARM64 compilation uses `-static -O2 -Wall -Wextra -Werror -Wno-unused-function -Wno-misleading-indentation -Wl,--build-id=none`. One CPU and 1 GiB address-space cap apply to the entire build/test process tree; no parallel compiler jobs, product Ninja or kernel build. Tools under `/srv/android/asus-target-rescue` were read only.

The Mac-only command below verifies compact delivery and existing public recovery inputs without a network connection. It reconstructs the zero-padded full-p10 bytes only in memory, checks all pinned prior local inputs, reads the previous public original recovery payload and prior commissioning image, checks stock equality and asserts public host refusal:

```
python3 -B scripts/verify_compact.py
```

The VM-only independent parser is `scripts/verify_container.py`, which requires the full raw/payload files retained there. This is a read-only image audit with a new JSON evidence output, not a device command. Existing reproduction/evidence should be read before any rerun. Tests use native memory/ordinary-file/socket adapters; test executables and the QEMU observer do not ship in the candidate image.

`ARTIFACTS.json` is the full VM inventory; compact delivery intentionally omits raw p10/payload/initramfs and native test binaries. `SOURCE_PINS.json`, `BUILD_SOURCE_PINS.json` and `DELIVERY_PINS.json` distinguish final delivered sources, build-audit source snapshot and final documents/evidence. Generated sources are included. No private SSH key was opened or copied; transport used the authorized key pathname and pinned host alias only.
