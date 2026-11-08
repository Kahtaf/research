# ASUS MT8163 4.9 bring-up: first experiment results

5 November 2026. **The control kernel builds. The ASUS board, exact panel and experimental touch adaptation compile; the ASUS kernel reaches final linking and stops at the unported charging interface. No installable ASUS image has been produced.** Android 17 / LineageOS 24 remains the final target.

The tablet is still running its original ASUS Android 7 firmware with the earlier debloat. No root, unlock, reboot, partition write or flash was performed. Play services and Play Store paths were verified again after the work.

## What changed

- Created a separate source/build experiment with immutable downloaded archives and pinned source revisions.
- Found that the audit's 4.9 `lineage-22.2` candidate is an incomplete BPF backport: it includes `linux/refcount.h` but does not supply it. The unmodified build fails there. It is retained as a reference, not repaired by adding a dummy header.
- Switched the hardware baseline to the same repository's Linux 4.9.337 `lineage-18.1` revision, `dc63af1741072236efb511499f1f0b9dd281d694`. The branch label does not change the Android 17 objective. Modern Android kernel features remain future work.
- Recovered **2,075 actual live device-tree properties** by streaming file contents. The audit's earlier `adb pull` copied zero files because sysfs properties report misleading sizes. That audit was explicitly corrected; its official boot-image DTB was valid throughout.
- Identified this unit's exact panel as **z380m_kd_rm68200g01**, touch as **GT6108**, charger as **BQ25896**, and backlight as **LP8557**. UG31xx is the optional cover battery gauge (`pack_bat`, present=0), not the main battery gauge.
- Added ASUS board DTS and battery settings from the GPL archive, registered the exact panel driver in the 4.9 LCM framework, and adapted its struct names and boot-panel lookup. The panel import is for the observed production board, HW_ID 3; EVB pin selection was removed. No fabricated hardware-ID function was added.
- Added a compile candidate for GT6108 to the existing Goodix driver. The version, coordinate and configuration register addresses and 240-byte configuration size match the stock driver. Kept ASUS GPIO wiring and disabled configuration-file loading for this controller. Actual power/reset, interrupts, tracking and suspend behavior are untested.
- Removed the other tablets' charger selections and Amazon dock/preloader-backup options from the ASUS config. Removed their RT551x audio DSP selection too. The remaining IDME and Karnak thermal selections are inherited, unvalidated work items; this is not a finished ASUS configuration.

## Actual build and verification results

| Check | Result |
|---|---|
| Unmodified `lineage-22.2` kernel | Fails missing `linux/refcount.h`; incomplete backport. |
| Pre-backport 4.9.337 control | **Full kernel link and Image.gz-dtb generation pass** after the compatibility patches below. This is an Amazon control build, not an ASUS image. |
| ASUS DTS against 4.9 SoC description | **Pass**, 61,942-byte standalone DTB, with legacy binding warnings. |
| Selected GPIO/address comparison | **13 checks pass** against the actual live DT, including display power/reset/backlight, Goodix and charger wiring. This checks data consistency, not electrical operation. |
| Exact ASUS panel object | **Pass**; its driver symbol is present in the ASUS aggregate drivers/built-in.o. |
| Goodix adaptation object | **Pass**; probe code is present in the ASUS aggregate drivers/built-in.o. |
| ASUS full build | Compiles to aggregate kernel object, then final link fails on **`chr_control_interface`** and **`chargin_hw_init_done`**. Both belong to the missing charger integration. No dummy definitions were added. |
| Original BQ25896 driver compile probe | Fails against 4.9 battery API. Mechanical type/log/header migration exposes missing ASUS battery/cover state (`old_charging_mode`, PAD/AC/COVER_OTG), BAT_thread integration and relocated headers. |
| Exported patches | Apply and replay against pristine source files; all 18 final source-file hashes match. |
| Boot or Android 17 runtime test | **Not performed.** |

The control compressed kernel is 7,270,109 bytes; with its four Amazon DTBs it is 7,701,499 bytes. This gives a useful size reference against the ASUS boot partition's 16,740,352 bytes, but does not prove the eventual ASUS boot image fits: the final ASUS kernel, selected DTB, MTK wrappers, ramdisk, Android boot header and page padding must be measured together.

The build uses the ARM64 Linux audit container and GCC 13 on this Mac. Warnings-as-errors remain enabled in the vendor code. Eight source-file compatibility changes fix declaration/indentation mismatches and guard an optional audio performance call when its implementation is disabled. They do not implement modern Android features. The control build still emits other warnings, including old linker RWX-segment warnings; it has not been declared runtime-safe or security-current.

Source patches and commands are repeatable. A byte-for-byte clean rebuild was not tested. The build runner now pins build version, timestamp and identity for future reproducibility; recorded control hashes describe the actual earlier build.

## The concrete blocker

The ASUS charger is more than an interchangeable I2C chip driver. Its stock implementation spans **4,339 lines** across the register driver, header and charging-control layer, and is coupled to ASUS battery policy, USB/OTG routing and optional powered-cover state. The newer MT8163 tree has a different battery structure and charger command interface.

A valid next change is a **pad-only BQ25896 integration**: preserve the pad's correct voltage/current/temperature limits and GPIO routing while deliberately separating optional cover features. Copying the old accessory state fields into the new structure or supplying empty functions to satisfy the linker would not establish correct charging behavior. Selecting Amazon's BQ24297/BQ25601 driver to obtain a binary would target the wrong hardware.

This is the current reason no ASUS kernel image is available. Compilation alone would still leave bootloader access, recovery, battery protection, backlight, thermal policy and graphics compatibility unproven.

## Continuation

1. Read [DRIVER-MATRIX.md](DRIVER-MATRIX.md), the final config and both charger probe logs. Trace the normal pad USB/DC charging path through the original ASUS `battery_common.c`, `switch_charging.c`, BQ25896 handlers and board GPIOs. Define the 4.9 interface and preserve the actual battery and JEITA policy; isolate absent-cover branches with real configuration, not fake return values.
2. Implement the BQ25896 port in a separate source change, reconcile the legacy control command table with the 4.9 enum, and build the complete ASUS kernel. Add meaningful boundary tests for register encoding, current/voltage units, command dispatch and temperature limits before any hardware use.
3. Replace/check inherited IDME and Karnak thermal assumptions, finish the LP8557 brightness path, establish touch power handling, and check the new r26p0 Mali UAPI against the stock r12p1 userspace. The old ASUS archive's included GPU source is older again; it cannot establish the installed driver's exact ABI by itself.
4. Only after the hardware kernel and recovery requirements are understood, build a minimal diagnostic initramfs and package a measured MTK boot candidate. Prove backups and restore access on this exact tablet before any custom boot. The prior audit's live GPT, not the firmware ZIP's mismatching scatter, defines partition offsets and limits.
5. Port and test the Android 17 kernel feature series and ASUS userspace integration on a suitable Linux platform builder. Google Play/Play services remain an acceptance requirement. Do not turn an older Android diagnostic image into the final target.

## Files and reproduction

- `patches/0001-build-compatibility.patch`: eight control-build source fixes.
- `patches/0002-asus-board-panel-touch.patch`: ASUS board, panel and experimental touch changes.
- `evidence/patch-manifest.json`: replay verification and final file hashes.
- `evidence/stable-source-provenance.json`: pinned base archive and checksum.
- `evidence/asus-import-provenance.json`: original ASUS file hashes and destinations.
- `evidence/stable-optional-boost/`: successful control build's final invocation and log; earlier baseline logs preserve preceding failures.
- `evidence/asus-pruned/`: final ASUS config/build invocation and exact link failure.
- `evidence/power-probe-original/` and `evidence/power-probe/`: untouched and mechanically migrated charger API probes.
- `evidence/live-dt-index.json`, `live-device-tree/`, `live-device-tree.dts`: actual live board evidence. Keep local; properties include unit identifiers and boot metadata.
- `evidence/board-wiring-verification.json`: selected live/candidate comparisons.
- `evidence/build-container-image.json`: actual Linux build image identity.
- `artifacts/asus-p00a-COMPILE-ONLY.dtb`: a compiled board description, **not a boot image**.

To reproduce on a pristine snapshot of `dc63af1741072236efb511499f1f0b9dd281d694`, apply patch 0001 for the control build and patch 0002 for the ASUS candidate. Use the audit container Dockerfile from the sibling feasibility spike, or the recorded image. With the spike mounted at `/work`:

```sh
python3 /work/scripts/build_kernel.py karnak_defconfig --label control-clean
python3 /work/scripts/build_kernel.py asus_p00a_defconfig --label asus-clean
```

The ASUS command is expected to fail at the charging link until that port is implemented. Do not run the initial archive extraction or one-shot import scripts on the already modified tree; the exported patches are the supported replay path.
