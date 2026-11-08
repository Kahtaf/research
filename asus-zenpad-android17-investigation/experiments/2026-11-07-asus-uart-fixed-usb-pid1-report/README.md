# UART-disabled kernel with exact RAM USB PID1 reporter

Question: after the concrete early UART-console change, can the existing RAM-only USB reporter reach PID1 and enumerate independently of SD and the retained-log header?

Status: one diagnostic image packaged offline. No kernel/C compilation, device/ADB/card/root-helper/private-input access, cloud changes, installer execution, reboot, independent review, or physical/fullOS GO. One isolated PLAN completed; its substitutions and limitations are recorded below. No subagents.

## Outputs

- `artifacts/candidate.img`: 7,970,816 bytes, SHA256 `8298badb09d9e91ee584eb6e27baf2054e660bbc5640443e9212f484f6fd590b`.
- `artifacts/candidate.p10.raw`: 16,740,352 bytes, SHA256 `c1fe664108ee8e2ef24edc9f0b3249589dc227f0ee8502b63e224930ee7fa541`; exact candidate plus zero padding.
- `artifacts/ramdisk.wrapped` and `artifacts/init`: byte-exact extractions of the existing USB report candidate, never rebuilt.
- `source/install.py`: current UART-disabled installer specialized only for actual candidate/full hashes, length, profile, and one appended known preimage `e965b75979e02e5514418e706f42b7874e4f72d72754864e5af0959646d2c9b0`. `execute()`, `Transport`, `Guard`, and legacy adapters are byte-identical. See `source/install.diff`.
- `evidence/packaging-receipt.json`: actual input/output hashes, extraction/container/static preservation assertions, header and DT receipts.
- `evidence/install-plan.json` and `evidence/plan-isolation-receipt.json`: one actual installer `main()` PLAN; no device contact or subprocesses. Public current candidate replaced the private stock input reader in memory; source checking was a no-op in memory to avoid root-helper reads. Private stock and dependency hashes were not validated by this PLAN. Delivered guards are unchanged.

## Actual ramdisk length correction

The wrapped ramdisk is 255,651 bytes (`0x3e6a3`), SHA256 `51e6d1dc0acb742522c69b29355d2d77d8ba73a3597fb8ad3354fa9f0c494e49`. Its exact MTK wrapper is 512 bytes, so the actual compressed payload is 255,139 bytes (`0x3e4a3`). Both the parsed wrapper field and actual extraction agree. Following the requested actual-payload-plus-base rule, `/chosen/linux,initrd-end` is **`0x4403e4a3`**, not the supplied `0x4403e6a3` (which includes the wrapper). This is the only DT byte change from the current UART-disabled candidate. The FDT header, every other property/token, gzip/raw Image, kernel wrapper, stock addresses, v0/2048 layout, and bootargs stay exact. The Android header changes only ramdisk length and required image ID; kernel/DT lengths remain equal, so their fields remain exact.

Static init is 597,856 bytes, SHA256 `d081c46dcf40684b35ec5f16bb4238b60662dd857a7211d46241e98f96ac872b`; static AArch64 ELF asserted. Existing run identity `9342cbf1-3bf0-44d4-b655-a1ca30146a99` and USB serial `P499342cbf13bf044d4b655` are reused unchanged. VID:PID is `0b05:4a49`; product is `ASUS-PID1:<actual uname.release>`. No expected-version substitution or UUID rebuild. The existing reporter creates a readonly tmpfs FAT12 `PROBE.TXT` with actual uname; it performs no SD/eMMC mounts or block writes, and attempts normal reboot 60 seconds after PID1 entry. Automatic return is unproven.

## Continuation for root

Root must freshly establish host absence of this reused USB identity before a trial. The Mac command is `system_profiler SPUSBHostDataType`; the older `SPUSBDataType` may misleadingly show nothing. Packaging did not perform this host observation. Root owns any separately authorized install, exactly one recovery entry, descriptor observation, and stock return. The next read-only root command, with output kept in this spike, is:

```sh
system_profiler SPUSBHostDataType > /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-uart-fixed-usb-pid1-report/evidence/root-fresh-usb-before.txt
```

Inspect that fresh output for absence of `P499342cbf13bf044d4b655` / `ASUS-PID1:` before proceeding. The prepared installer entry point for root's separately authorized installation phase is:

```sh
python3 /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-uart-fixed-usb-pid1-report/source/install.py --execute
```

That command is documented only; it was not run and grants no physical/fullOS GO. The preserved installer uses the existing authenticated transport. Its appended preimage is supported by parent install run `097b74f7-ed11-45bc-94ca-a12c547ab3d7` and public `../2026-11-07-asus-early-uart-disabled-trial/evidence/physical-result.json`. No private run material was consulted.

Prior cached CPU0 matched the early MMIO32 UART read before the logger. With console disabled, later cached PCs mapped to current `disp_irq_handler+0x530` and `asus_p00a_pmic_adc+0x154`; capture epoch and causality remain unproven. No SD/RAM marker was observed. The estimated interval to the new stock kernel was 32.906–32.963 seconds versus nominal PID1 60 seconds. This does not establish a watchdog reset; a timebase discrepancy or deliberate PID1 reboot remains possible. Stock Android USB return boot identity was `de110e8a-fd75-41ae-8f90-6ac881b96085`; parent evidence reports original BOOT/SYSTEM/DATA untouched. This artifact supplies one independent PID1 discriminator after the UART change.

To inspect packaging, read the receipt and `source/package_probe.py`. The package script refuses an existing candidate; the PLAN script refuses a second PLAN. No rebuild or further probe is required by this spike.
