# Exact ASUS P00A_2 LK handoff audit

Status: **one host-correctable packaging conflict proved in the frozen Linux 4.9 probe's recovery path**. LK removes the ramdisk wrapper and relocates the compressed payload to `0x44000000`; the probe's retained header `initrd=` token instead tells Linux to start 512 bytes later. No image was changed. This is static evidence and a bounded semantic model, not a physical boot result or authorization.

The added stock-kernel rescue question has a different result: **the old DT's `initrd=0x44000200,0x200000` is replaced, not preserved, by this LK**. The rescue header has no `initrd=` token. No 2 MiB clamp exists in the traced recovery ramdisk copy or initrd-property writes. Crossing 2 MiB in a future armed image is therefore not, by itself, the proposed old-DT truncation mechanism. That future image was not supplied or validated here.

## Exact inputs and scope

All inputs were read locally. All writes are beneath this spike. No device, USB, ADB, SSH, cloud, build, dependency installation, bootloader/security change, or nested-repository mutation occurred. No agents were delegated. Existing observer findings and physical recovery/reset decisions were not reopened.

| Input | SHA-256 |
|---|---|
| Exact LK, 418,048 bytes, mapped at `0x41e00000` after its 512-byte wrapper | `c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765` |
| Frozen probe-r2 image, 8,880,128 bytes | `48bb6efa1620cb380037e53b53cfa560e38cd23b95211c8634616ce94fd6ce48` |
| Probe zero-padded to p10, recomputed without writing a padded file | `25812e7dde39ec37e3f4c9438341cc29f2b2e7dce61e4b88d0886cd9dd075b16` |
| Compiled `Image.gz-dtb-combined-r1`, 7,696,186 bytes | `d4094bcff6c763af7f1c01ccd3d612a988f96de13f78b492b808cc76c0ac929f` |
| Unarmed target-rescue delivery, 9,541,632 bytes | `93d647ea58784aefe4104cb0cbddbac04fe6169b30923ad63c5684e0dc920419` |
| Rescue's exact stock wrapped kernel | `b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880` |

The script independently compares both saved device LK backups with the exact LK prefix and verifies their remaining bytes are zero. It compares the rescue's wrapped kernel with the saved initial stock recovery kernel. Full paths, sizes, hashes, source pins, and prior runtime-receipt hashes are in [input-receipts.json](evidence/input-receipts.json). Prior successful stock/control runtime evidence is context, not evidence that this 4.9 kernel booted.

The 4.9 compressed kernel stream remains byte-identical to the compiled input: SHA-256 `acd66b0e487c9b3cf6170b471847e5b6b83478ca50a00ce6c7cbcae8401951e5`. Product-r3 was not substituted.

## Method and strength of evidence

Names are inferred from exact instructions, arguments, and library behavior; LK has no recovered debug symbols here. File offset is `VA - 0x41e00000 + 512`.

* [reachable-disassembly.txt](evidence/reachable-disassembly.txt) decodes from function entries and actual branch/fallthrough targets. It excludes literal pools and jump tables from the instruction stream. Both conditional edges are retained: this is a static reachability union, not a runtime trace. Calls are separate boundaries. [reachable-calls.json](evidence/reachable-calls.json) lists those boundaries.
* [handoff-disassembly.txt](evidence/handoff-disassembly.txt) supplies additional raw bytes and PC-relative/literal/GOT annotations. Its linear register annotations are candidates only; joins, conditional execution, and stale registers must not be treated as proven state.
* [handoff-model.json](evidence/handoff-model.json) parses the exact images and applies the manually traced layout/scan/copy/property rules. Key instruction bytes are asserted. Fourteen negative/boundary checks pass.
* This is **not CPU emulation**. Unicorn was unavailable in the existing venv; QEMU ARM commands were not on PATH. No dependency was installed. The semantic model explicitly substitutes ordinary copy/string/FDT contracts and host raw zlib inflation, and stops at platform/secure-monitor boundaries. It neither executes LK's inflate engine nor fabricates a full runtime DT or command line.

## 1. Recovery reaches the common path; bitness comes from preloader state

`0x41e1de74` dispatches through the ten-entry halfword table at `0x41e1de78`. Entry 2 resolves to `0x41e1e006`. The recovery header load is called at `0x41e1e012 -> 0x41e04564`. Returned nonnegative header status reaches `0x41e1e022`; the recovery payload load is `0x41e1e038 -> 0x41e04980`. On its nonnegative return, `0x41e1e058` branches to `0x41e1de90`. This report starts with the already-established valid-header/loading path, not a new security-path review.

The 64-bit flag is `0x41e701a8`, via GOT base `0x41e6500c`, slot `+0x2a0`. Its selector is `0x41e02c74`, called at `0x41e02cf8`. It reads the preloader argument field at `[*[GOT+0x148]+0x14c]`. The byte table at `0x41e02c9a` routes values 0, 1, 4, 5 to `0x41e02cb4` (store 1); 2, 3 and values above 5 route to `0x41e02ca0` (store 0). Thus the header's textual `bootopt=...` is not what selects this flag in the traced path. Its actual preloader value remains an offline input boundary.

With the flag nonzero, recovery's `0x41e1e028 -> 0x41e1e064` calls `0x41e052b4`, which returns the constant scratch address `0x45000000`. That becomes the payload loader's destination argument. The common handoff is called at `0x41e1df58 -> 0x41e1de3c -> 0x41e1ce78` with:

* r0 = Android `kernel_addr`, `0x40080000`;
* r1 = Android `tags_addr`, `0x4e000000`;
* r2 = LK's accumulated command-line buffer, returned by `0x41e1ccb0`;
* r3 = the platform machine value; it is not the DT pointer for the 64-bit transfer;
* stacked arguments = Android `ramdisk_addr` and the recognized wrapper's payload size.

## 2. MTK wrappers are skipped before the ramdisk's final relocation

`0x41e04218` checks MTK magic `0x58881688`, then compares up to 32 name bytes at `+8` using `0x41e25d08`. That comparison calls the ASCII lowercase helper at `0x41e252a0`; it is case-insensitive. Success returns the word at wrapper `+4`; bad magic/name returns -1.

Both exact images contain `KERNEL` and uppercase `RECOVERY`. The recovery loader asks for lowercase `recovery` at `0x41e04a5c`, so **the uppercase wrapper is recognized**, not treated as raw ramdisk data.

Address-specific layout:

| Instructions | Validated operation |
|---|---|
| `0x41e04654–0x41e046ac` | Calculate rounded kernel/ramdisk page counts; provisional rootfs source is scratch + rounded Android kernel size. |
| `0x41e049e6`, `0x41e049f0–0x41e049f6` | Recognize kernel wrapper; decrement read destination by 512. Compressed kernel therefore begins at scratch, not scratch+512. |
| `0x41e04a06–0x41e04a0e` | Decrement provisional rootfs source by the same 512. |
| `0x41e04a4e` | Read image data after the Android header page into that destination. Storage return is an explicit boundary. |
| `0x41e04a5c–0x41e04a7a` | Recognize recovery wrapper, save its payload length, advance rootfs source by 512. |
| `0x41e1de96–0x41e1dea4` | Use recognized nonzero payload length; load destination from Android `ramdisk_addr`. |
| `0x41e1deaa–0x41e1deac` | `memcpy(header.ramdisk_addr, adjusted_source, payload_size)`. **No +512 is added to the destination.** |
| `0x41e1df4a–0x41e1df54` | Pass payload size and Android destination to the common handoff. |

| Value | Frozen 4.9 probe | Unarmed stock-kernel rescue |
|---|---:|---:|
| Kernel wrapper load address | `0x44fffe00` | `0x44fffe00` |
| Compressed kernel start | `0x45000000` | `0x45000000` |
| Ramdisk wrapper staging address | `0x45757600` | `0x45720600` |
| Compressed ramdisk staging address | `0x45757800` | `0x45720800` |
| Final compressed ramdisk start | **`0x44000000`** | **`0x44000000`** |
| Compressed bytes copied | 1,177,520 (`0x11f7b0`) | 2,064,968 (`0x1f8248`) |
| Final end, exclusive | **`0x4411f7b0`** | **`0x441f8248`** |

The earlier linear candidates `0x41e048d2/0x41e04906` are in the normal boot payload loader. Recovery uses the corresponding actual instructions above. Likewise `0x41e1f390–0x41e1f6f8` is the fastboot RAM `cmd_boot` handler: its memory/overlap strings and guards at `0x41e1f410/480/494/4c0/67a/6de/6e8` are **not recovery-loader guards**. They are not used to certify recovery layout.

## 3. Appended DT selection and gzip loading

At `0x41e1ce9a`, a nonzero bitness flag branches to `0x41e1cf48`. `0x41e1cf5e–0x41e1cf64` requires `kernel_addr & 0x7ffff == 0`. Both images' `0x40080000` passes. Failure reaches the log at `0x41e1d00e` and permanent loop at `0x41e1d01c`.

`0x41e1cf66–0x41e1cf94` scans backward byte by byte from `scratch + Android.kernel_size` for bytes `d0 0d fe ed`. This is **last-magic selection**, not board-compatible DT selection. On success, `0x41e1cf96–0x41e1cfa2` copies the tail, rounded up to four bytes, to the tags address using the byte-copy helper `0x41e1ce64`. The scan uses Android kernel size including its wrapper, although scratch already points beyond that wrapper. The model preserves this detail rather than silently subtracting 512.

| Quantity | Probe | Rescue |
|---|---:|---:|
| Selected DT source | `0x457476b5` | `0x45710ec3` |
| Actual FDT totalsize | 63,725 | 62,482 |
| Initially copied tail bytes | 64,240 | 62,996 |
| Gzip stream bytes | 7,632,565 | 7,409,347 |
| Input length supplied to decompression | 7,632,562 | 7,409,345 |
| Decompressed file bytes | 17,275,392 | 16,963,568 |

The rounded scan subtracts 3 probe trailer bytes / 2 rescue trailer bytes from the supplied gzip length. **This is not a demonstrated decompression failure.** `0x41e1e4a8 -> 0x41e1e428` skips the gzip header; `0x41e1e396` initializes raw inflate with window bits -15. The code at `0x41e1e3ce–0x41e1e3d4` requires return 1 (stream end); it does not validate the gzip trailer there. Host raw-zlib modeling finishes both exact streams, leaving 5 / 6 supplied trailer bytes unused and reproducing the full host-decompressed image hashes. This tests byte compatibility under an explicitly substituted inflate implementation, not LK runtime allocation or execution.

`0x41e1cfd6–0x41e1cfe2` passes source scratch, destination Android `kernel_addr`, the computed input length, and output capacity `0x1c00000` (28 MiB). A nonzero decompression return leads to `0x41e1cff2` and loop `0x41e1cff6`. Successful decompression branches to `0x41e1ceaa` with r7 still pointing at the relocated DT. The probe's decompressed file ends at `0x410f9a00`; its ARM64 Image `image_size` is 18,767,872, reserving through `0x41266000`. LK does not use that field in this traced handoff to calculate the inflate capacity or choose the entry; it uses the Android address. The maximum inflate span ends at `0x41c80000`, below LK base `0x41e00000`.

At `0x41e1ceaa–0x41e1cece`, LK checks DT magic. `0x41e1cef2–0x41e1cef6` compares tags+FDT totalsize against `*[GOT+0x44]`. That global is a runtime framebuffer base assigned in platform initialization (`0x41e03130–0x41e03146`), **not a fixed host-proven RAM limit**. LK copies the FDT into place at `0x41e1cf06`, opens it in a buffer of `min(framebuffer_base - tags, 1 MiB)` at `0x41e1cf36`, then checks it at `0x41e1d020`. Failure returns to the handoff wrapper's loop. Actual allocation/framebuffer position is not supplied by the image.

## 4. Final initrd properties and command-line precedence

The common frame pushes 36 bytes and allocates `0xc54`, so `[sp+0xc78]` and `[sp+0xc7c]` are exactly the two original stacked initrd arguments. This establishes values by calling convention, not log-string guessing.

`0x41e1d0fc` locates `/chosen`. `0x41e1d100–0x41e1d136` byte-swaps the passed ramdisk address and calls property setter `0x41e26c28` with length 4 and name `linux,initrd-start`. `0x41e1d140–0x41e1d176` adds the passed payload size and similarly sets `linux,initrd-end`, length 4. For the probe those bytes are `44 00 00 00` and `44 11 f7 b0`. Existing host DT values are replaced. For the rescue, the properties are added to its original DT, which has neither property in `/chosen`.

Header command-line handling is separate:

1. `0x41e1ded6–0x41e1dee0` formats header+`0x40` with literal `%s` and a **100-byte buffer**, preserving at most 99 characters. Probe header length is 95; rescue header length is 68. Neither is truncated.
2. `0x41e1dee6 -> 0x41e1ccbc` appends that text with a separating space to LK's buffer at `0x41e5b964`, subject to its 1,022-character combined-length check. The literal initial buffer contains console/earlycon/root/vmalloc/hardware arguments; it contains no `initrd=`. The header is appended before the common handoff's later additions.
3. `0x41e1d474` appends `androidboot.serialno=` from GOT `+0x1fc`, which resolves to serial buffer `0x41e5b8a0`. The serial provider is `0x41e20550`, called at `0x41e1e17a`. `DEVICE_SERIAL_REDACTED` is the expected device value from saved evidence, not a literal proved by the LK file. Recovery mode 2 branches at `0x41e1d4a2` to `0x41e1d8cc`, adding `androidboot.mode=recovery`.
4. `0x41e1d630/0x41e1d644` create `atag,cmdline`. **`0x41e1d650–0x41e1d664` sets `bootargs` to the complete LK command-line buffer, length strlen+1. It does not read or merge the original `/chosen/bootargs`.** `0x41e26c28` replaces an existing property via resized storage and memcpy, or adds it if absent.
5. `0x41e1d68e` packs the DT. After these writes, the two optional DT hooks at `0x41e1d67a/0x41e1d688` are NOPs with zero GOT slots `+0x5c/+0x27c`. They are not unexamined active callbacks that rewrite initrd again.

Other additions include boot reason/profiling, ASUS `lk.ro.*` values, factory/CTS flags, and fuse-ready state. The ASUS buffer appended at `0x41e1d4dc` is built at `0x41e2062c` using fixed keys `ro.isn`, `ro.config.versatility`, `ro.config.CID`, `ro.config.idcode` and runtime values from `0x41e204b0`. Its values are not modeled. The meta-mode `rdinit=sbin/multi_init` addition at `0x41e1d9ac` is reached for modes 1, 4, 5, 6, **not recovery mode 2**. The recovery hibernation table selects the reset/clear path, not the normal resume-string path. No traced literal addition constructs a later `initrd=` override. A complete runtime command line cannot be promised without the runtime string providers; the model explicitly assumes they do not inject another `initrd` token.

### Confirmed 4.9 packaging conflict

The retained probe header token is `initrd=0x44000200,0x11f7b0`. The exact 4.9 source pins show `setup_machine_fdt()` before `parse_early_param()` in `arch/arm64/kernel/setup.c:256–258`. The DT scanner reads initrd properties and bootargs; `arch/arm64/mm/init.c:65–80` registers `early_param("initrd", early_initrd)` and overwrites start/end. Embedded IKCONFIG extracted from the exact 4.9 Image confirms `CONFIG_BLK_DEV_INITRD=y`, bootloader command line, and neither FORCE nor EXTEND. Hash-pinned excerpts are in [source-excerpts.txt](evidence/source-excerpts.txt).

Thus, on the successful traced handoff without an extra runtime override, Linux first obtains correct DT range `0x44000000–0x4411f7b0`, then changes it to **`0x44000200–0x4411f9b0`**. This skips 512 bytes of the compressed stream and extends 512 bytes beyond the copied payload. At the requested start, the exact moved bytes begin `3a7cf5f5b31b67faeec5f0f2858d7337`, not gzip magic or a newc header. This conflict is deterministic in the packaging and LK data flow; it does not claim which physical symptom would follow.

**Concrete correction, not applied:** preferably remove the explicit `initrd=` token from the Android header and let LK's start/end properties supply the actual payload range. Alternatively change it to `initrd=0x44000000,0x11f7b0` (same 95-byte total header length). Keep Android `ramdisk_addr=0x44000000`, both MTK wrappers, and the compressed ramdisk/kernel unchanged. For consistent host DT metadata, remove its stale bootargs token or correct it, and set its host initrd properties to `0x44000000/0x4411f7b0`; this LK will overwrite those DT fields anyway. A DT-only correction would **not** fix the retained bad header token. Proposed strings are machine-readable in `handoff-model.json`.

### Stock-kernel rescue and the 2 MiB question

Its stock DT contains `console=ttyS0,921600n1 root=/dev/ram initrd=0x44000200,0x200000`. Its Android header contains no `initrd=`. The old DT bootargs are replaced as above, and LK writes the actual wrapper length: currently start `0x44000000`, end `0x441f8248` (2,064,968 bytes). The 32,184-byte margin to 2 MiB is not consumed by a fixed 2 MiB LK cap in this path.

The model exercises payload sizes `0x1fffff`, `0x200000`, `0x200001`, and `0x240000`; the traced copy count/end calculation follows each size with no 2 MiB clamp. This does **not** validate an unbuilt armed image, its final partition size, memory overlaps, or its runtime. Re-run exact parsing on the final armed bytes. No stock-kernel or DT edit is supported merely by the old embedded DT token. The rescue's stock Image has no embedded IKCONFIG marker; this audit does not claim to have reconstructed all stock-kernel configuration/behavior from the LK trace. The specific old-DT-token preservation/truncation hypothesis is refuted at the LK bootargs replacement boundary.

## 5. Kernel entry and the DT register boundary

At `0x41e1d78e`, the bitness flag selects the 64-bit route. `0x41e1d790–0x41e1d798` calls `0x41e1ce30` with r0=`0x40080000`, r1=`0x4e000000`, r2=0, r3=1. The wrapper preserves these across logging and calls ARM code at `0x41e1b86c`.

[smc-arm-disassembly.txt](evidence/smc-arm-disassembly.txt) proves the register shuffle and SMC at `0x41e1b880`:

| Register immediately before SMC #0 | Value |
|---|---|
| r0 | `0x82000200`, literal at `0x41e1b8f4` |
| r1 | `0x40080000`, intended kernel entry |
| r2 | `0x4e000000`, relocated DT pointer |
| r3 | 0 |
| r4 | 1 |

This is an AArch32-to-secure-monitor handoff, not an LK `br` directly into AArch64. **LK proves the DT in r2 at SMC; the secure monitor must establish the AArch64 entry contract, conventionally x0=DT and x1–x3=0. Those post-SMC registers, EL, cache/MMU state and eventual PC are not established by this binary audit.** Returning from the SMC falls into a loop. No physical boot/reset conclusion follows from that loop.

## Remaining bounded unknowns

* Runtime preloader bitness field, storage/heap success and actual readable/writable RAM mappings.
* Framebuffer/DRAM allocation and resulting DT expansion limit; platform DT fixups `0x41e1d040 -> 0x41e0534c`, `0x41e1d04e -> 0x41e05414`, memory topology provider `0x41e1d076 -> 0x41e055f4`, count provider `0x41e1d0bc -> 0x41e055e4`, and fixup `0x41e1d0e4 -> 0x41e0594c`. They precede initrd writes but can fail or change other DT state. No full final `/memory`, reservations, or dynamic consys placement is fabricated.
* Actual libfdt growth/allocation success and complete platform ATAG payload contents. Setprop failure returns out of common handoff; its wrapper loops at `0x41e1de4c`.
* Runtime serial/ASUS property/boot-reason strings, exact resulting command-line length, and preexisting LK buffer state. The model uses observed contracts, not stubbed evidence of a physical success.
* `0x41e1d628 -> 0x41e20720`, platform teardown calls at `0x41e1d6d0/6d6/6da`, and the actual secure-monitor transition at `0x41e1b880`. These are stop boundaries, not no-op emulation proofs.
* The 4.9 kernel's eventual compatibility, userspace execution, and physical return behavior; the final armed rescue artifact's size and layout. None is resolved by the host model.

The original fixed reservations and Image reserved-end checks remain relevant, but do not determine runtime allocations. The 120-second userspace request and physical Power/reset behavior remain entirely outside this audit.

## Reproduce locally

From the workspace root, using the existing venv (no installation or network):

```sh
2026-11-05-asus-boot-access-audit/.venv/bin/python 2026-11-06-asus-lk-linux49-handoff/scripts/disassemble_handoff.py
2026-11-05-asus-boot-access-audit/.venv/bin/python 2026-11-06-asus-lk-linux49-handoff/scripts/capture_reachable.py
2026-11-05-asus-boot-access-audit/.venv/bin/python 2026-11-06-asus-lk-linux49-handoff/scripts/model_handoff.py
```

The parser is pinned to both exact current image hashes and fails if either is changed. It must not silently follow a rebuilt delivery. Model checks cover wrapper case/name/magic, kernel alignment, absent/multiple DT magic, malformed gzip method, insufficient inflate capacity, wrong versus corrected initrd starts, removal of the override, and the 2 MiB crossing. All outputs are small evidence files; no new image or kernel artifact is generated.
