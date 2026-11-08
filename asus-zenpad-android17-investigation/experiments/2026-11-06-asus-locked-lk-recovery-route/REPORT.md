# Exact locked LK: independent original-recovery restoration

**Verdict: an existing OEM-assisted LK route reaches a full original-p10 write without working Android or userdata, without unlocking, and without an image-signature/TEE decision on the traced write path. Ordinary `flash:recovery` with the session flag clear is denied. The enabling OEM compatibility query is `getvar:sofia_support`; it changes a RAM flag and must not be classified as read-only.**

**There is an important scope failure: this route implicitly attempts a whole-p10 TRIM before writing. It does not satisfy a literal “no erase” requirement.** The exact command/address trace confines the requested TRIM and full write to p10 under the expected geometry; it does not prove the real card's behavior or physical success. No separate erase command is needed or proposed. If *all* erase/discard operations are forbidden, use the independent RAM alternative below; do not quietly reinterpret the requirement.

This closes the **offline lock/authorization uncertainty**, not the physical p10 qualification or complete userdata rollback. A parent-supervised same-stock qualification is now concrete if the parent accepts the intrinsic p10 TRIM. No physical GO, writer implementation, arming, unlocking, seccfg change, full updater, or device action is supplied.

## Evidence and exact inputs

The workspace AGENTS.md was read. This is a new spike; earlier artifacts and nested repositories were preserved. All work was local and sequential. No actual device/ADB/USB/fastboot/root access, reboot, private/ access, private calibration/security/key contents, cloud operation, AOSP/Ninja/build mutation, package installation, or delegate was used. No whole SYSTEM read/hash/copy occurred.

| Input | Exact identity |
|---|---|
| Public OEM `2026-11-05-asus-boot-access-audit/sources/firmware/lk.bin` | 418,048 B; SHA-256 `c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765` |
| Original recovery, `artifacts/device-backup/{initial,verify}/recovery.bin` in that spike | Both independently hashed here: 16,740,352 B; `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20` |
| Geometry, adopted saved receipt | p10 / recovery, major:minor supplied by parent 179:10; start 160184, 32696 sectors, last sector 192879; bytes `[82014208,98754560)` |
| Saved real fastboot queries | `secure=yes`, `unlocked=no`, product `ASUS8163_EW_380`; 2026-11-06 02:27 UTC |
| Parent preservation and reset contract | Public receipts adopted; private preservation payloads not reopened; standalone p20 writer still unapproved |

LK is Thumb after the 512-byte wrapper, at base `0x41e00000`; file offset = VA − base + 512. GOT base is `0x41e6500c`. The prior exact-LK handoff audit independently matched the public prefix against **both** saved LK copies and checked zero tails. This audit pins/adopts that receipt rather than reopening whole raw device LK as though it were necessarily public firmware.

[Input hashes](evidence/input-pins.json), [saved query summary](evidence/saved-identity.json), [31 instruction fixtures](evidence/emulation.json), [1,444 executed instruction pins](evidence/instruction-pins.json), [executed disassembly](evidence/executed-disassembly.txt), and [registration table](evidence/registration.json) are supplied. Original instruction bytes were rechecked against the public LK. `route-disassembly.txt` provides the wider annotated windows. Linear annotations and `discovery-disassembly.txt` are discovery aids: pools, tables and ARM regions can decode as misleading Thumb. The verdict uses traced branches and executed slices, not those candidate annotations alone.

## Registration, lock gate, and the unexpected session flag

The actual registration routine `0x41e1e500` stores prefix, prefix length, flag A, flag B and handler at node offsets `+4,+8,+0xc,+0x10,+0x14`. Executing init and registration recovered 30 commands. Relevant entries:

| Registration call | Prefix | Handler | A / B |
|---|---|---|---|
| `0x41e1ea6c` | `getvar:` | `0x41e1f288` | 1 / 0 |
| `0x41e1eaaa` | `flash:` | `0x41e23338` | 1 / 0 |
| `0x41e1eb9a` | `download:` | `0x41e22a24` | 1 / 0 |
| `0x41e1ec30` | `boot` | `0x41e1f390` | 1 / 1 |
| `0x41e1ed22` | `oem emmc_read_partition` | `0x41e2284c` | 1 / 0 |

Dispatcher `0x41e1e83e–0x41e1e8cc` checks secure USB download at `0x41e3b218`. Its alternate branch checks `0x41e392dc(1)`. Both routes admit A=1. B=0 reaches `blx r3` at `0x41e1e872` without requiring unlocked state. B=1 calls `0x41e3ab10`; zero produces `FAILnot allowed in locked state` at `0x41e1e8c6`. That same getter supplies `getvar:unlocked` at init `0x41e1eb3c`; `getvar:secure` uses `0x41e3aae4`. Secure-query and secure-USB predicates are not assumed identical: both secure-USB outcomes were tested for the relevant registrations.

Consequently **`flash:` and `download:` pass the dispatcher while locked; `boot` does not**. The denied `boot` fixture never enters `cmd_boot`. An unlocked-positive control reaches its stub, solely to validate the fixture. No unlocking is performed or proposed.

Inside `flash:`, `r9` receives the pointer at GOT `+0xd8` = `0x41e73358`. With a nonempty ordinary recovery image:

1. `0x41e2339a–0x41e233a0` loads that RAM flag. Nonzero goes to `0x41e233a4`.
2. Zero goes to `0x41e234ba`, which calls `0x41e3ab9c("recovery", &permission)` at `0x41e234be`.
3. Failure emits `failed to get download permission ...` through `0x41e2370a–0x41e2371c`.
4. Even if the policy function succeeds and returns `permission=1`, `0x41e234c8–0x41e234ce` reloads **the global RAM flag**, not the permission local at `sp+0x2c`. If still zero it emits `download for partition 'recovery' is not allowed` via `0x41e234d2–0x41e234e4`.

This is a concrete pre-content denial. Original ASUS bytes cannot rescue this branch through a signature: the buffer is not authenticated or passed to the raw writer. Synthetic missing/present policy and image-lock 0/1 cases all reach no partition lookup or storage operation with the flag clear.

The exact existing setter is in `getvar`:

- `0x41e1f2d2–0x41e1f2e0`: `strncmp("sofia_support", argument, strlen(argument))`.
- `0x41e1f2e4`: unequal skips the store.
- `0x41e1f2e6–0x41e1f2ec`: load GOT `+0xd8`, store **1** into `0x41e73358`.
- Then ordinary variable lookup/reply continues. An empty `OKAY` can therefore accompany a real side effect; the reply payload is not the flag.

Only the exact full compatibility name is considered here, not permissive prefix variants. `product` leaves the flag clear in the control. The setter calls no storage, lock setter, key verifier or TEE. It affects LK RAM; do not assume USB disconnect alone clears it. It enables broader flash/erase behavior, so parent tooling must keep a strict command allowlist. It is **not** `oem flash_all_start`, a signature command, or an unlock sequence.

With the flag set, the handler skips that policy gate. Executed full-stock and same-length modified-image fixtures both reach the same writer. There is **no stock-only signature exception** to prove here: the traced write route does not authenticate either. This says nothing about later kernel boot authentication or custom-image bootability. The registered `signature` handler, `0x41e21820`, itself reports “Signature command not supported”; it is not an additional recovery signing step.

## Download completeness and raw-image boundary

For exact command `download:00ff7000`, the download handler parses 16,740,352 and emits `DATA00ff7000` through `0x41e22aaa–0x41e22aba`. Fastboot init advertises `0x08000000` (128 MiB), but that advertised number is not treated as a universal parser safety guarantee.

`0x41e22adc` asks reader `0x41e2149c` for the initial 28-byte header. Because this exact total is below `0x06400000` (100 MiB), reader `0x41e2155a–0x41e2156a` actually requests the **entire 16,740,352 bytes** from USB into the existing download buffer on that first call. It checks returned count against the total and the sign bit. The underlying USB loop `0x41e1e588` uses requests of at most 16 KiB and returns a short count/error on failure; hardware completion is a declared stub boundary.

The exact original first word is ordinary Android magic, not sparse `0xed26ff3a`. The non-sparse branch `0x41e22af2–0x41e22b28` consumes the buffered remainder, restores the base pointer, publishes length at `0x41e7842c`, and sends `OKAY`. The full fixture's RAM buffer hash equals the original recovery hash. No storage operation occurs during that exact raw download.

**Do not generalize this to all downloads.** The sparse branch contains storage writes, including `0x41e22cc2 -> 0x41e1416c`, during `download:`. No sparse conversion, package, compression or generic flashing frontend is within this candidate.

Injected short and error reads set fastboot state `0x41e711c4` to 3 via `0x41e2154c–0x41e21554`; the response helper suppresses `OKAY` unless state is 1. The upper handler nevertheless continues and can publish the requested length after failure. **The length global alone does not prove a complete download.** Parent must require its exact transmitted count **and** the final successful download response; any timeout/error ends the transaction with no `flash:` or automatic retry. Fresh-session handling remains a physical transport gate.

## Exact p10 path, bounds, TRIM, write, and return

With exact argument `recovery`, the handler avoids `singlebootloader`, GPT/package, bulk flash and raw hardware-area aliases. The virtual `zimage`/`ramdisk` transform `0x41e21f24` returns without changing recovery or its bytes. Non-sparse dispatch at `0x41e23488` calls raw writer `0x41e21844` with the original buffer and full length.

| Address / edge | Original behavior |
|---|---|
| `0x41e2185e -> 0x41e13fe4` | Resolve `recovery` through public name table at `0x41e58f94`, stride 0x50. Executed alias lookup returns index 9. This index is not an eMMC hardware-area ID. |
| `0x41e2186c -> 0x41e14074` | Obtain runtime partition start in bytes; invalid start rejected. Name-to-runtime geometry is a remaining fresh-device guard. |
| `0x41e21882 -> 0x41e14044` | Obtain storage hardware area; expected 8 = eMMC user area. This is not Linux p8. |
| `0x41e2194c–0x41e2195a -> 0x41e21896` | Recovery shares the boot-image check: compare **7 bytes** against `ANDROID!`; this is a weak header check, not verification. |
| `0x41e218b8 -> 0x41e140b4` | Obtain partition capacity; reject if round-up-to-512(download length) exceeds it at `0x41e218bc–0x41e218d4`. |
| `0x41e21994–0x41e2199e -> 0x41e141b8` | For recovery, request erase callback over **whole partition capacity**, even for shorter images. |
| `0x41e219b8–0x41e219c4 -> 0x41e1416c` | Write exactly supplied byte count from the original RAM buffer at partition start. |
| `0x41e219c8–0x41e219ce` | Compare signed-extended 64-bit write return to supplied size. Mismatch emits `FAILflash write failure`; success emits `OKAY` through `0x41e219da`. |

The pre-write calls at `0x41e233a4/0x41e233a8` are also bounded: `0x41e059ec` reads timer MMIO `0x10008048`; `0x41e05a74` performs arithmetic conversion. They contain no storage or security decision and are substituted with deterministic values in the fixture.

The storage erase callback is not assumed to be the default no-op. eMMC setup `0x41e19686–0x41e1968a` installs GOT `+0x10` = `0x41e191f5` at device `+0x18`. `0x41e141d6–0x41e141da` calls it. The default `0x41e1ac4c` returning -1 is a different, fallback callback.

Executing `0x41e191f4` and its real command-construction routines with synthetic expected card fields proves the requested sequence:

- hardware partition selection `0x41e1911c` maps area 8 to user area 0; fixture starts already in that area, so no switch is needed;
- `0x41e17ea0`: MMC command 35, argument **160184**;
- `0x41e17eec`: MMC command 36, argument **192879**, inclusive;
- `0x41e17f38`: MMC command 38, argument **1** — TRIM, per the captured local Linux MMC constants.

The callback checks sector alignment, nonzero length and device range. There is no outward rounding to an erase group in the traced command construction. Block size, capacity, high-capacity addressing and TRIM support were synthetic fixture inputs, not fresh observations of the card. If TRIM support is absent, the fixture issues start/end setup but does not issue command 38 and returns failure. **The upper raw writer ignores the erase return and still writes**, proven by the negative fixture. Real eMMC command execution, status, erase effectiveness and power-loss behavior remain untested.

The actual aligned write chain is `0x41e1416c -> device+0x14 -> 0x41e1aca8 -> block+0x68 -> 0x41e191cc -> 0x41e18360`. eMMC registration supplies the write callback at `0x41e19672–0x41e1967c`; the generic aligned writer supplies a single 32,696-sector request at sector 160184, buffer unchanged. The executed storage fixture stops at `0x41e18360`, with expected controller 0, area 8 and no head/tail read-modify-write for these aligned values. The remaining controller/DMA/chunk I/O is a hardware boundary; no durable flush or readback is inferred from its return.

Full-length input covers every p10 byte, including the original tail. A shorter-by-512 fixture still TRIMs full p10, writes 512 fewer bytes and returns `OKAY`: tail restoration is **not automatic**. Oversize by one, wrong header and missing partition are rejected before erase/write. Zero length returns `OKAY` without writing anything. Thus `OKAY` alone is never the acceptance criterion.

For the exact raw recovery branch, no GPT, preloader, boot area, p20, p26, para, or other partition write call is reached. This is a call-scope result with expected geometry, not a universal promise about faulty firmware/hardware. Whole-p10 TRIM is expressly present.

## Other OEM writers do not supply a fixed safer p10 command

The 30 registrations contain readback and partition-list commands, not a dedicated fixed original-recovery restore command. `flash:emmc_write_userdata` reaches `0x41e223f0` from `0x41e23692`; it writes eMMC **user area**, not specifically Linux userdata p26, using a mutable 64-bit global offset at `0x41e734e0`, 64 KiB chunks and no p10 identity/capacity guard in that handler. Its write returns are ignored before `OKAY`. The boot1/boot2 siblings use hardware areas 1/2. These are unsuitable substitutes for a bounded p10 restoration and are excluded. `flash_all`, GPT/resize, key/lock and FRP paths are likewise excluded. No such mechanism was built or executed.

## Smallest parent action and conditional same-stock qualification

**Next action: reproduce the offline fixtures and decide whether the candidate may include the implicit whole-p10 TRIM.** This audit provides no permission decision. If the parent retains literal no-erase scope, the candidate fails that scope and no LK test is appropriate. If the parent explicitly includes that intrinsic operation, the following is the smallest concrete test to qualify next, while original stock BOOT/SYSTEM and a nearby independent recovery/fastboot fallback remain usable:

1. Establish actual nearby user/power/fallback and exclusive idle transport. Freshly identify exactly one `0bb4:0c01`, serial `DEVICE_SERIAL_REDACTED`, product `ASUS8163_EW_380`, interface `ff/42/03`, one bulk endpoint each direction, matching LK/build, secure yes/unlocked no. Saved receipts are not fresh checks. Reconfirm recovery start 160184/count 32696/size 16740352, 512-byte sectors and user hardware area; reconcile with Linux 179:10 when available, without depending on userdata for future use.
2. Ensure the baseline p10 is already the exact original image through full readback. If current p10 is a rescue image, this is a replacement, not a same-stock test: preserve and qualify an alternate bootable route first. Locally verify the original input's exact length/hash; preserve both known copies. Do not hash/copy SYSTEM again.
3. In the parent-owned bounded transport, permit only the exact firmware-specific compatibility query, exact raw download, `flash:recovery`, and recovery readback plus the agreed identity queries. Do not execute `erase:`, sparse handling, bulk aliases, GPT, other partitions or retries. `getvar:sofia_support` is the explicit RAM-gate change, not a harmless identity query. It neither proves success nor alters seccfg in the traced handler.
4. Send the exact `download:00ff7000`; require matching `DATA00ff7000`, send all 16,740,352 original bytes with exact counts, then require final download `OKAY`. On timeout, short count, disconnect, unexpected response or identity drift, **do not send `flash:`**. The previous Mac fastboot reboot timeout means generic CLI transport is not presumed qualified; existing bounded libusb read/query code is a read-only reference, not a tested writer.
5. Send only `flash:recovery`. The intrinsic whole-p10 TRIM and full write occur here. Record raw protocol and elapsed results. Any ambiguous completion is UNKNOWN; no blind retry or reboot into a possibly damaged recovery. A power loss after TRIM can leave p10 unusable despite identical source bytes.
6. While still in LK, independently read **all 16,740,352 bytes** through the existing qualified `oem emmc_read_partition recovery` route. That OEM route streams raw bytes then `OKAY`, not a standard DATA frame. Require exact count, trailing framing and whole SHA-256 equality, not the OEM hash shortcut. Preserve a new receipt and do not overwrite earlier artifacts. Parent then qualifies fresh recovery entry/menu/cancel/return, without selecting wipe in this p10 test. Direct entry and the OEM reset are separate phases with their own previously reviewed para/cache/data effects.

No physical write or readback happened here. Transport full-download success, card completion/persistence, actual direct recovery entry and the fallback remain open. Same-stock success would qualify this p10 restoration route; it would **not** prove post-A17 FDE/reset success or all power-loss safety.

The accepted eventual rollback remains: original SYSTEM, original BOOT, idle rescue transactions, independent original p10 restoration/readback, direct OEM recovery reset, then stock FDE/startup and second-boot persistence acceptance. p20 stays unchanged until that intentional OEM reset, which can change its whole length. No new p20 writer is introduced.

## If no-erase is mandatory: smallest independent RAM alternative

A separate **one-shot, fixed original-p10 restorer running from RAM in an already bootable trusted rescue environment** is the bounded alternative. It would preload and hash the entire original 16 MiB recovery in tmpfs; verify serial/geometry/179:10/unmounted exclusive access and the expected prior image; open only p10; overwrite exactly its length without discard/erase; fsync/close/reopen/full-readback; and return an unambiguous receipt before any reboot. It must have no arbitrary path/offset/partition command and no p20 role. This is a design prerequisite, **not an implementation or approval**; existing RSC roles remain unchanged.

Its concrete prerequisites are a separately approved and tested fixed artifact, a qualified RAM execution/transport entry independent of userdata, a recoverable interruption plan, and a known bootable route kept intact while changing the other slot. Running recovery is already resident in RAM, but writing its on-disk slot removes that persistent fallback if interrupted. A separately qualified rescue in BOOT while restoring original RECOVERY can retain one persistent rescue route, followed by original BOOT restoration from a still-running qualified environment. Existing daemon recovery pins and SYSTEM-before-BOOT transaction ordering must be revalidated for that choreography; it is not currently authorized by roles 0/1. Keeping stock recovery intact while first qualifying a temporary rescue in BOOT is another possible ordering only if that rescue's BOOT entry and return are independently demonstrated. Locked `fastboot boot` is **not** the RAM-entry solution here; its dispatcher requires unlocked state.

This audit does **not** block the first R3 RAM-only kernel trial. That trial still needs an actual nearby fallback. It also does not demand an already-proven post-A17 rollback before the first transition: same-stock p10 qualification plus original recovery entry/reset baseline gives bounded prequalification and a solid candidate, while the actual post-A17 transition remains a later acceptance test.

## Reproduction and declared limits

From the workspace root, run sequentially:

```sh
2026-11-06-asus-stock-userdata-recovery/.venv/bin/python -B 2026-11-06-asus-locked-lk-recovery-route/source/disassemble.py
2026-11-06-asus-stock-userdata-recovery/.venv/bin/python -B 2026-11-06-asus-locked-lk-recovery-route/source/emulate.py
2026-11-06-asus-stock-userdata-recovery/.venv/bin/python -B 2026-11-06-asus-locked-lk-recovery-route/source/collect_evidence.py
```

All 31 cases pass: registration; public recovery alias; locked secure/nonsecure dispatch and unlocked control; normal versus compatibility getvar; four clear-flag policy cases; full original/modified image, missing policy with flag set, bad magic, oversize, short length, missing partition, short storage write, failed erase, zero length; complete/short/error download; real lower storage TRIM construction with/without advertised support; aligned sector write construction.

Each fixture permits named original-code ranges only, asserts on an unexpected PC or interrupt, limits each emulation call to 100,000 instructions/two seconds, and maps 34 MiB. One CPU instance runs at a time; measured peak process RSS was about 385 MB, below 1 GiB. No large packages or workloads were started. All storage and USB are synthetic. Stubs include ordinary string/memory/format/allocation/log routines, registration-time platform setup and state providers, dispatcher secure/lock return values, top-level partition geometry/read-write results, and lower-level card/host state, unsigned 64-bit division, command completion/status or block-write completion. Exact per-case stub addresses and executed-PC sets are in `emulation.json`. Storage layers are tested separately: top-level I/O is stubbed in the flash fixtures, whereas lower storage fixtures execute its real wrappers/callbacks down to command construction. This is original machine-code execution with declared boundaries, not physical evidence or a model substituting all of LK with Python.
