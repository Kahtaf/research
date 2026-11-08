# Retained startup trace: implementation handoff

**An opt-in diagnostic patch is staged and its affected objects compile.** The
exact normal-Android and recovery kernels corroborate the OEM reader ABI. The
writer checks the final handed-off DT, Linux memory reservations and existing
OEM header before writing. Physical retention and readback of this new trace
remain untested; this is not a claim that a trace was captured.

## Deliverable and scope

Apply `retained-boot-trace.patch` to an isolated copy of the e9 source, then
resolve `diagnostic.config` into the unchanged e9 resolved config. The option
`CONFIG_ASUS_P00A_RETAINED_BOOT_TRACE` defaults off. Its only intended config
delta is that boolean. `patched/` contains the seven reviewable resulting files;
`source/` contains read-only source snapshots and supporting implementation.

The implementation adds one 176-line ARM64 writer, a small interface, build
wiring, a setup call, five direct startup checkpoints and one printk insertion
hook. It performs no storage I/O. Bootargs, DT, timers, CPU setup, drivers,
watchdog behavior and the existing pstore configuration are unchanged.

The printk hook is necessary because a console callback is filtered by the
existing `silent` bootargs. It copies records at `log_store`, independently of
console filtering. Stored text has a newline appended when necessary; timestamps,
priority prefixes and a replay of earlier printk records are not implemented.
Allocation, console registration and a dependency on timekeeping are avoided.

## Exact shipped reader, not an assumed source revision

Original recovery SHA-256:
`902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`.
Its wrapped kernel is
`b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880`;
decompressed Image is
`db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a`.
The saved initial **normal-Android boot.bin contains that same wrapped kernel
byte for byte**; see `evidence/stock-boot-kernel.json`.

`inspect_stock.py` validates all 70,337 embedded kallsyms names, markers and token
indices and retains the relevant machine code in `evidence/stock-reader.disasm`.
The reference public `mtk_ram_console.c` guided inspection; its optional pstore
branch was not assumed to describe the shipped kernel.

Material binary facts:

- `ram_console_late_init` at `0xffffffc000f412f0` registers `last_kmsg` with
  `ram_console_file_ops`. `ram_console_file_open` at `0xffffffc0006952e0`
  supplies `ram_console_show` to `single_open`.
- `ram_console_early_init` at `0xffffffc000f41350` maps 128 4 KiB pages,
  records physical base `0x44400000`, and uses size `0x80000`.
- It recognizes signature `0x43474244`, validates the header and copies
  all `0x80000` bytes to its old buffer **before** resetting Linux text.
- Header offsets are: size `0x28`, Linux reason `0x2c`, console `0x30`,
  log start `0x34`, log size `0x38`, console size `0x3c`; header size is 64.
- `ram_console_check_header` additionally checks PL/LK aligned section
  relationships. These extra compiled checks are not present in the supplied
  reference C's header check; the patch observes the compiled contract.
- Both initialization and `ram_console_show` use **0x400** for the aligned
  Linux reboot-reason extent. The reader checks console bounds and emits
  `[log_start, log_size)` followed by `[0, log_start)` from the console.
  It does not take the reference C's optional pstore-console branch.

The writer preserves the signature, offsets, sizes, padding and PL/LK payloads.
It requires the existing layout to match the shipped initializer's PL/LK or
512-byte fallback calculation. It zeros the Linux reason area and resets only
text lengths. It deliberately refuses absent, corrupt or changed OEM layouts
rather than manufacturing a header over unknown firmware-owned sections.

The text is append-only and freezes at capacity to preserve the earliest
checkpoint. `log_start` stays zero; the exact stock reader then emits the
initialized prefix `[0, log_size)` for both partial and full buffers. No reader
modification is required. A typical 512-byte fallback gives console offset
`0x600` and capacity 522,752 bytes, but **no live header with these offsets was
read in this task**; actual offsets are checked at runtime.

## Range, mapping and publication

The exact e9 appended FDT and original stock FDT agree on reserved ram_console
`0x44400000..0x44480000`. The e9 resolved config is
`10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`;
existing PSTORE/PSTORE_RAM/PSTORE_CONSOLE are enabled with zero configured
address/size. The new writer does not configure or reuse a ramoops format.

Initialization occurs immediately after `paging_init()` in `setup_arch`.
Before accessing the header it requires root `asus,p00a`, one exact enabled
`mediatek,ram_console` reservation, two-cell identity-addressed reserved-memory
bindings, no overlapping static reserved node, and neither `no-map` nor
`reusable`. It checks the entire range lies in Linux memory and checks every
4 KiB page is mapped and reserved. It excludes overlap with kernel extent,
final FDT and actual initrd. Dynamic reserved-memory allocations already use
memblock's reservation exclusion. This does not assume the template `/memory`
is the final LK-fixed RAM map.

The inspected e9 `map_mem` maps non-NOMAP memory with normal cacheable linear
attributes, including reserved pages. The writer uses that existing `__va`
mapping only; it creates no competing Device or uncached alias. Exact source
snapshots for `paging_init`, memblock, cache helpers and their assembly macros
are retained in this spike.

For every append, payload stores are cleaned with
`__clean_dcache_area_poc` before updating the single aligned 32-bit `log_size`.
That exact helper uses cache-line clean to PoC and terminates in **DSB SY**.
The header line is then cleaned with the same completion barrier. During
initialization, zero `log_start` is cleaned before zero `log_size`, preventing a
reset between those steps from exposing `log_start > log_size`. Writes use an
IRQ-safe raw trylock, perform no printk and drop a contending/reentrant record
rather than wait. Cache-clean latency and additional RAM writes necessarily
perturb diagnostic timing.

These are architectural completion guarantees, not proof of byte survival
through this tablet's return/reset sequence. An abrupt reset during a write
can lose the incomplete append; firmware can still overwrite retained RAM.
Hardware retention remains the fact the parent's single trial must establish.

## Observable boundary

The first positive marker is:

`ASUS-e9-retained-v1 01 paging_init returned; trace ready`

It establishes entry into C, completion of early FDT parsing, early parameters,
ARM64 memblock/reserved-memory setup and paging, and successful logger guards.
It precedes device-tree unflattening, bootmem setup and IRQ/timer initialization.
Direct subsequent markers identify setup_arch return, before/after init_IRQ,
and before/after time_init. Thus marker 05 without marker 06 bounds a failure
inside time_init only if the retained record itself remains valid. The APXGPT
mismatch is neither patched nor asserted to be the cause.

Unobservable before marker 01: LK/secure-monitor transfer, early assembly,
initial MMU/exception state, start_kernel entry, Linux banner, early DT parsing,
memblock setup and paging failures. Earlier printk records are not replayed.
A missing marker also permits a refused runtime memory/header guard or lost
retention; the refusal is ordinary printk while the retained writer is disabled.
Absence alone does not prove Linux never executed. printk text not committed
by log_store, lock-contending records and text after capacity are not captured.

## Bounded checks and continuation

- All four affected objects compiled with the existing GCC/toolchain and exact
  e9 generated headers/config, with the diagnostic boolean supplied as a
  compile define. No warnings or errors. Only the refined logger was recompiled.
  See `evidence/compile.json` and `evidence/final-logger-compile.json`.
- C build assertions check the real header size and field offsets. One offline
  layout check pins ten exact stock instruction words and verifies the stock
  reader lengths for a short marker and a full append-only buffer. These are
  layout checks, not simulated boot or retention results.
- The patch applies cleanly to disposable original-file copies and produces
  exactly the seven staged files; `evidence/patch-check.json` pins all pre/post
  hashes. Source/config preservation receipts accompany the compile results.

Compiler outputs are isolated under
`/srv/android/asus-linux49-retained-boot-trace-20261107`; the original
`/srv/android/asus-bmc156-full-kernel-r1/kernel` and `out` were read-only inputs.
No make, config regeneration, full Image build, candidate, flash, device access,
ADB/USB/card/root helper, private data, calibration/table access, cloud lifecycle
or process management, bootloader/security change, or subagent was used.
All local writes are within this new spike.

Parent continuation: review the actual patch and runtime refusal conditions,
then own one isolated config resolution/build/trial using the existing e9
bootargs/DT/helper and the device-operation lock. Confirm the resolved config
has just the diagnostic boolean delta before the build. On the immediate stock
Android return, use the already-authorized stock last_kmsg collection path and
look for the literal `ASUS-e9-retained-v1`; this task performs no collection.
Retain the complete returned text and exact candidate/boot identity. A positive
marker is the new execution evidence; a missing one retains the limitations
above and is not grounds for another guessed OS/timer change.
