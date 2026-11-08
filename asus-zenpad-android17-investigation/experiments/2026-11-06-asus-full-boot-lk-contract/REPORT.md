# Future full Android 17 BOOT: exact LK contract replacement

Status: **implementation complete; host tests pass; PLAN_ONLY by default; parent integration pending**. No actual full AOSP BOOT was available or claimed. Both generated BOOT fixtures are deliberately **NONBOOTABLE**, with no `/init`. No device, ADB, USB, root, flashing, cloud lifecycle, active build-source mutation, calibration access, or goal change occurred. The only remote work was read-only source inspection/capture over the already authorized builder SSH connection.

## Delivered replacement

- `scripts/package_full_boot.py`: callable packager and CLI, strict input contract, default report-only mode.
- `scripts/lk_contract.py`: 92-byte header selection, compiled IKCONFIG gate, three-property DT update, exact scanned-tail/raw-inflate semantic check.
- `scripts/boot_memory.py`: corrected unwrapped ramdisk extent, actual `Image.image_size`, original fixed/dynamic reservations, static RAM containment and LK inflate/DT-buffer limits.
- `evidence/replacement.patch`: reviewable change against the untouched current full packager/memory helper, plus the new contract module. `evidence/integration-receipts.json` pins preimages, replacement bytes and unchanged dependencies.
- `tests/`: packaging boundaries, actual extracted SDK37/kernel source bodies compiled with ASan/UBSan, and patch application to a temporary isolated copy.
- `source/` and `evidence/source-excerpts.txt`: hash-pinned primary sources captured from the builder. Reproduction needs no network.

The patch was applied **only to a temporary copy inside this spike**, using the original `probe/bootformat.py`, `probe/fdt.py`, wrapper inputs and provenance. The resulting synthetic image matched the standalone output exactly. The active packager and frozen R2 image remain unchanged.

## The chosen header is 92 bytes

```text
bootopt=64S3,32N2,64N2 build_version=3 androidboot.boot_devices=soc/11230000.mmc enforcing=1
```

The packager accepts the five exact current AOSP input arguments (`bootopt`, `build_version`, `androidboot.hardware`, `androidboot.fstab_suffix`, `androidboot.boot_devices`), optionally `enforcing=1` and/or `androidboot.selinux=enforcing`. It rejects missing, conflicting, duplicate or unreviewed arguments, including **every** explicit `initrd=` override, even one with the corrected address. It forms the reviewed header from those semantics; it never blindly truncates the incoming string. The long BoardConfig cmdline remains unchanged.

Why the shorter header preserves the required behavior:

1. **Hardware:** the exact LK binary's initial command-line buffer at `0x41e5b964` contains `androidboot.hardware=mt8163`. The audit asserts the complete literal, including the console/earlycon/root/vmalloc arguments, against the binary. Duplicating hardware in the header is unnecessary for this pinned LK. SDK37 `property_service.cpp` imports `androidboot.*` and maps `ro.boot.hardware` to `ro.hardware`.
2. **Fstab:** real `fs_mgr_get_boot_config()` falls back from DT/properties/bootconfig to the kernel cmdline. `GetFstabPath()` tries `fstab_suffix`, then `hardware`, then `hardware.platform`. With the suffix omitted and hardware supplied by LK, it finds `fstab.mt8163`, including early ramdisk locations. The packager requires at least one supported ramdisk path containing the exact reviewed regular-file fstab, SHA-256 `04179d23e76be8755f6452319e05cc89f2438b51fcc539cb76695c9c65c57e75`. It rejects Android DT fstab/selection overrides and gzip trailing bootconfig. This is an explicit pinned-fstab boundary; future fstab changes require review, not silent normalization.
3. **Boot devices:** `androidboot.boot_devices=soc/11230000.mmc` remains explicit. Real SDK37 `GetBootDevices()` supports this cmdline fallback. Tests exercise the actual function body, not a Python reimplementation of its selection logic.
4. **SELinux:** both real compiled kernels contain `CONFIG_SECURITY_SELINUX=y`, `BOOTPARAM_VALUE=1`, `DEVELOP=y`, and no runtime-disable option. In this 4.9 source, `int selinux_enforcing` is zero-initialized with DEVELOP enabled; the actual `__setup("enforcing=", enforcing_setup)` changes it to 1. **The parent’s 96-byte candidate would omit that early kernel setting.** The replacement explicitly includes `enforcing=1`. Real SDK37 `StatusFromProperty()` returns enforcing unless a permissive cmdline/bootconfig request is present; `IsEnforcing()` also returns true for non-permissive builds. `SelinuxSetEnforcement()` fatally fails if it cannot establish the requested mode. Thus no explicit `androidboot.selinux=enforcing` token or kernel config patch is needed for this input profile. This proves intended settings, not successful runtime policy loading or preservation against later root actions.
5. **Bootopt/build_version:** a recorded search of 48,366 kernel `.c`, `.h`, `.S` files found no parser for these boot arguments. Matches were unrelated firmware fields, `unknown_bootoption`, and similarly named identifiers. `init/main.c` passes unknown unqualified `key=value` tokens into init's environment. The saved LK audit establishes that its 64-bit flag is selected from preloader state, not the header's textual bootopt. **Both tokens are retained anyway**; the implementation does not need to assume their irrelevance outside this source boundary.

The actual captured tree has SDK version 37 in both `trunk_staging` and `cp2a` release flag values. This supports the source context; it is not a claim that a completed full SDK37 product or policy has passed validation.

## Normal BOOT applicability, not recovery-name inference

The exact LK is SHA-256 `c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765`, mapped at `0x41e00000` after its 512-byte wrapper. `capture_normal_reachable.py` extends the saved entry/branch-based disassembly with the normal header and normal payload functions. It does not decode literal pools as execution. `audit_normal_lk.py` checks the original binary bytes, table entry, branch reachability, PC-relative name argument and relevant common-path instruction pins.

- Dispatch table entry 0 resolves to `0x41e1e070`, then `0x41e1e078`. Normal header loading is `0x41e1e084 -> 0x41e042bc`.
- With the preloader 64-bit flag nonzero, `0x41e1e0d6 -> 0x41e052b4` obtains scratch `0x45000000`; normal payload loading is `0x41e1e0aa -> 0x41e047e4`.
- The normal loader checks `KERNEL` at `0x41e0484a`, adjusts the load/source addresses by -512 at `0x41e0485a/0x41e0486e`, and checks **ROOTFS** at `0x41e048c0`. Its name argument is independently resolved from the literal at `0x41e04964`, not inferred from string presence. The recognized payload size is stored at `0x41e048c8`; the ramdisk source advances 512 at `0x41e048da`.
- On the successful loading path, `0x41e1e0ca` reaches common `0x41e1de90`. Common copy destination is `header.ramdisk_addr` at `0x41e1dea4`; copy occurs at `0x41e1deac`. The header's `0x44000000` is the **compressed gzip payload destination**, not a destination retaining the MTK wrapper.
- The shared `snprintf` limit is 100 at `0x41e1dedc`, so at most 99 non-NUL bytes survive. Shared DT start/end setters and bootargs replacement are separately byte-pinned. Header initrd is omitted; three host DT properties are set consistently with `0x44000000 .. 0x44000000 + compressed_ramdisk_length`, using the same 32-bit bounds as LK.

Existing full-BOOT templates correctly contain `KERNEL` and `ROOTFS`. Recovery probe wrappers remain `RECOVERY` and were not changed. The saved stock-wrapper provenance is retained as its own historical receipt; it is not relabeled as the newly qualified stock rollback BOOT.

This is static reachability plus explicitly bounded semantic modeling, **not instruction emulation**. Calls to storage/security/runtime providers are boundaries. Normal mode here does not prove signature acceptance or a real device traversal of the path.

## Memory and byte preservation

The previous memory calculation counted an extra 512 bytes at the destination. The replacement reserves `[0x44000000, 0x44000000 + payload_length)`. The fixed ram-console reservation begins at `0x44400000`: a compressed ramdisk of exactly **4,194,304 bytes** fits by the end-exclusive rule; 4,194,305 bytes fails. This is a fixed-reservation fit check, **not** an invented LK 4 MiB or old DT 2 MiB copy clamp.

The validator uses the ARM64 `image_size` (18,767,872 for these inputs), not merely the decompressed file length (17,275,392). It preserves and checks all original FDT memreserve entries and fixed reserved-memory ranges, rejects overlaps and static RAM escapes, and keeps the exact 2 MiB/alignment-2 MiB dynamic consys node. Its dynamic placement remains explicitly unverified. It checks LK's 28 MiB inflate capacity and a conservative 1 MiB DT expansion envelope; actual framebuffer/DRAM fixups remain runtime gates.

Only `/chosen/bootargs`, `/chosen/linux,initrd-start`, `/chosen/linux,initrd-end` change in the DT. All other tokens/properties and the reservation table remain identical. Charging opt-in is rejected. The compressed Image stream and compressed ramdisk are compared byte-for-byte before/after packaging. Wrapper bytes remain identical except their payload lengths. Android v0/page-2048 geometry, component padding, SHA-1 component ID, header version, empty second component and the **16,740,352-byte** partition limit are checked. Nonzero extended command lines, unreviewed header tail, input trailers and invalid padding fail closed.

The backward DT scan includes the retained 512-byte kernel wrapper size, just as the pinned LK does. A later FDT magic causes rejection. The exact rounded copied-tail calculation produces a supplied gzip length three bytes shorter than the full gzip stream for both fixtures; host raw-zlib modeling still reaches stream end, leaves five trailer bytes unused and reproduces each full decompressed Image exactly. This is compatibility evidence for the traced algorithm, not proof of LK allocation/inflate execution on hardware.

## Synthetic evidence

Test-only cpio contains a warning marker, exact reviewed `fstab.mt8163`, and the real R3 probe `/init` bytes stored as **non-executable reference data** named `fixture-reference-init.bin`. It contains no `/init` or fallback init program. The Android image name and output filename are also NONBOOTABLE. The packager rejects it in full-product mode. No fixture is labeled flashable.

| Fixture kernel | Output bytes | Synthetic output SHA-256 |
|---|---:|---|
| Real compiled r1 | 8,257,536 | `dc1b4baa669d709c53e6678989adefcb91405b543d15282954e67c9b1cbe2add` |
| Real compiled product-r3 | 8,257,536 | `26b1de1f8d5405fd2e58f6a0457fd5415db4f7037cc8d91b314b47055754e3e7` |

Both use a 555,280-byte test gzip ramdisk, unchanged compressed SHA-256 `95203220926a8fda7cbed82054988e8591e2dcd15bd2f97b0ce50f51ed4f17ba`, ending at `0x44087910`. Their manifests include padded partition hashes without storing padded copies. The actual R3 1,177,520-byte probe ramdisk was also modeled independently in memory: its first byte at `0x44000000` is the gzip stream's first byte, its end is `0x4411f7b0`, and the old +512 location is not gzip magic.

Everything generated is inside this spike, approximately 34 MiB total. No SYSTEM/data image was read/copied; no new full-image file was written on the builder.

## Tests and reproduction

`evidence/checks.json` records all eight reproduction steps passing. Coverage includes **26 Python test groups**, **14 exact-source-body checks under each of two init build settings** with ASan/UBSan, pinned normal-LK reachability/model checks, and a deterministic integration-patch test. Source-body tests substitute host file/property/bootconfig/DT I/O and platform dependencies; they are not a boot of Android init.

Boundary checks include 99th-vs-100th required content, absent/conflicting/duplicate arguments, duplicate/corrected/old `initrd=` rejection, early enforcing, exact 4 MiB and one-byte overflow, real `Image.image_size`, FDT/fixed-reservation overlap, RAM end, changed dynamic reservations, charging opt-in, appended-DT selection, wrapper names/lengths, Android ID, padding, partition overflow after wrappers, gzip trailers/bootconfig, and rejection of synthetic data in full-product/default mode.

From the workspace root:

```sh
python3 2026-11-06-asus-full-boot-lk-contract/scripts/run_checks.py
```

This uses the already existing audit venv for Capstone and local `/usr/bin/clang++` for source-body tests. No install, server, network, device or build-source edit is needed. `capture_sources.py` is an optional **read-only SSH refresh** of primary evidence, not part of routine reproduction. If sources have changed, review/repin rather than treating new results as the same proof.

## Concrete parent integration steps

1. Review `evidence/replacement.patch`, `integration-receipts.json`, this report and the tests. Confirm the real target's preimages and unchanged helper/wrapper hashes still match; `build_review_patch.py` and `test_integration_patch.py` check the local originals without changing them.
2. Apply the reviewed patch to the intended full-build continuation scripts only when the parent is ready. It replaces `scripts/package_full_boot.py` and `scripts/boot_memory.py`, adds `scripts/lk_contract.py`, and reuses the existing `probe` helpers, `inputs` wrapper files and `evidence/stock-wrapper-provenance.json`. No active AOSP/BoardConfig/kernel patch is needed for this header contract.
3. Wait for an actual validated SDK37 full product. Run the existing complete product, Google/Services/root/hardware-preservation and policy gates. This packager verifies the report's BOOT hash and packaging inputs; it does **not** replace those gates or certify an arbitrary AArch64 ELF as genuine SDK37 init.
4. Invoke the replacement with the original four path arguments (`--aosp-boot`, `--build-report`, `--kernel`, `--out`). Default `PLAN_ONLY` validates in memory and writes only a manifest. A later explicit `--mode PACKAGE_UNTESTED` emits the actual untested candidate. Keep output directories new. `SYNTHETIC_FIXTURE` is solely for the marked no-init fixtures and must never enter transport.
5. Recheck final actual compressed ramdisk size and reservations. If it exceeds 4 MiB, packaging must stop; do not bypass the reservation, reinstate +512 or alter the fixed carveout here. Any needed reduction/layout redesign belongs to a separate parent-coordinated change. Unknown future cmdline args, different fstab or kernel configuration also require review.
6. Record final actual BOOT/DT/config hashes and rerun the exact normal-LK contract/model on those bytes before any parent physical decision. Maintain signature/locked-LK acceptance, secure-monitor transfer and runtime validation as separate gates. The first 4.9 physical test still requires nearby fallback. This spike provides no physical GO or device command.

## Remaining physical boundaries

The real full BOOT signature is invalid/unproved for locked LK; storage/security acceptance has not been demonstrated. Preloader bitness, complete runtime arguments, runtime framebuffer/DRAM fixups, later provider overrides, dynamic consys placement, and actual kernel/userspace/hardware operation remain unproved. The pinned common handoff supplies the DT in AArch32 **r2** at SMC; establishing AArch64 **x0**, EL, cache/MMU state and entry PC remains a secure-monitor boundary. No unbounded monitor reverse engineering was attempted and no hardware-success claim follows from this host work.
