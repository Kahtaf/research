# Parent handoff — complete, review/integration pending

**PLAN_ONLY default. All eight offline check steps pass. No actual device/ADB/USB/root/flashing action, active-source edit, private calibration/key read, cloud resource change or goal change occurred.** Read [REPORT.md](REPORT.md) for complete evidence and integration steps.

## Ready for review

- [Replacement patch](evidence/replacement.patch): replace `scripts/package_full_boot.py` and `scripts/boot_memory.py`; add `scripts/lk_contract.py`.
- [Integration preimage/dependency hashes](evidence/integration-receipts.json).
- [Passing reproduction receipt](evidence/checks.json): 26 Python groups, 14 exact-source checks under each of two init settings with ASan/UBSan, exact normal-LK audit, isolated patch-application/determinism test.
- Reproduce offline: `python3 2026-11-06-asus-full-boot-lk-contract/scripts/run_checks.py` from workspace root.

## Contract to integrate

92-byte header:

```text
bootopt=64S3,32N2,64N2 build_version=3 androidboot.boot_devices=soc/11230000.mmc enforcing=1
```

Exact LK supplies `androidboot.hardware=mt8163`. Real SDK37 fstab selection falls back from omitted `fstab_suffix` to hardware and selects the pinned `fstab.mt8163`. Real SDK37 defaults to enforcing without `androidboot.selinux=enforcing`; the actual 4.9 DEVELOP config needs `enforcing=1` for early kernel enforcement, so the 96-byte candidate without it was not used. No kernel patch is needed for this contract. Both bootopt/build_version are retained.

Normal BOOT has its own proved static reachability: mode-0 table entry reaches `0x41e1e070`; normal header/payload calls target `0x41e042bc` / `0x41e047e4`; successful return branches `0x41e1e0ca -> 0x41e1de90`. Its ramdisk name is **ROOTFS**, not RECOVERY. Existing full-BOOT templates are already correct. The normal loader strips 512 at source and common memcpy uses Android `ramdisk_addr=0x44000000` as destination.

Omit all header initrd tokens. Update only three chosen DT properties, with 32-bit start/end matching LK. Preserve compressed Image and ramdisk bytes, wrappers except size fields, Android component ID/padding/geometry, partition limit, Image.image_size and all fixed/dynamic reservations. Exact 4 MiB compressed ramdisk fits below ram_console; +1 byte fails. Do not restore R2 installation or modify its frozen image.

## Parent action boundary

Review/apply the patch when ready; run the original product/policy/Google/root/hardware gates on a real completed SDK37 product. This packager only verifies the supplied BOOT hash and packaging contract. Unknown cmdline values, changed fstab/config or oversize ramdisk fail closed and need review. Default CLI writes a manifest only; explicit `--mode PACKAGE_UNTESTED` emits a future real candidate after those gates. The patch was tested only on an isolated copy and has not been applied to the active target.

Two 8,257,536-byte **NONBOOTABLE synthetic fixtures** exist under `artifacts/`, using real r1/product-r3 kernels, test-only cpio and no `/init`. Never place them in transport. Complete spike is approximately 34 MiB; no SYSTEM/data copies or builder image writes.

Hardware remains unproved: signature/locked-LK acceptance, complete runtime arguments, RAM/framebuffer fixups, dynamic consys allocation, SMC r2-to-AArch64-x0 transfer, and real kernel/userspace operation. First physical 4.9 test still requires nearby fallback, owned by parent. No physical GO is implied.
