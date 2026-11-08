# Android 17 hardware-kernel continuation

Hardware candidate remains unbooted. Follow-ups on 5 November local / 6 November UTC cleared fastboot transport with an alternate libusb client, created verified exact-unit backups and demonstrated on-demand root on stock Android. Google components remain intact, and two further optional packages were reversibly disabled (17 total). The actual ASUS Android 17 init/ADB product and real-kernel header export now compile. Current device/root evidence is in the sibling boot-access-audit and root-hardware-validation STATUS.md files; build evidence is in android17-device-product/STATUS.md. A validated locked-bootloader/restore path and new-kernel hardware tests remain required.

## Implemented offline

- A real pad-only BQ25896 regmap/charging-command integration with propagated I/O errors, bounded voltage/current settings and temperature/fault guards. The diagnostic device tree **does not permit battery charging**. The optional cover and OTG are unsupported. Read-only stock charger diagnostics confirm the selected chip ID and GPIO routing; this does not test the new driver on hardware.
- Power tests execute the production command engine under a simulated register transport. All **6,672 checks pass** with address/undefined-behavior sanitizers. Earlier tests caught four failures; their logs remain available. IRQ/concurrency, ADC calibration, watchdog recovery and actual battery behavior remain untested.
- ASUS thermistor parameters (AUXADC0, 390 kOhm pull-up, 1.8 V, curve 6; all 34 curve pairs match the ASUS source), with failed ADC reads propagated instead of reported as a cold temperature. IDME and the Karnak-specific thermal selection are disabled. The shared virtual-sensor implementation stays enabled because other 4.9 thermal drivers unconditionally use its helpers; there are no Amazon virtual-zone nodes in the ASUS DT.
- Touch GPIO85 has one owner: the GT6108 consumer. The new charger no longer also requests it.
- A deferred LP8557 controller-enable bridge using the original ASUS register sequence, correct DT match and GPIO43. Actual brightness continues through MediaTek PWM/AAL. **19 sequence/failure checks pass**; no real backlight has been driven by this code.
- Stock Mali library disassembly proves a legacy ioctl (`0xc0108000`) and version request **10.2**. The existing r20p0 driver supports that ioctl and UK10.2 atom translation; r26p0 does not. r20 selection and a full local link pass are evidence of a plausible ABI path, not working graphics.
- Corrected duplicate RAM nodes and reserved-region differences introduced by combining the ASUS board with the 4.9 SoC include. The candidate uses this unit's observed usable bank and reserved secure pool, with the original ASUS CMA option enabled. Bootloader fix-ups and secure-world compatibility are still untested.

## Build correction and reproducibility

The local source/output filesystem is case-insensitive. The original archive contains **12 groups of names differing only in case**. A subsequent full rebuild failed at xt_hl.o; earlier local link results therefore cannot establish a correct complete kernel. `scripts/build_kernel.py` now refuses this filesystem. Do not build or publish the Mac source snapshot as a complete kernel source distribution.

**The clean GCP build passed.** It extracted the original pinned archive on Linux ext4, checked its SHA-256, applied all three patches, and built Image.gz-dtb. All 19 changed-source hashes match the reviewed patch manifest. The resulting 7,200,108-byte kernel+DTB has SHA-256 `b66d2c249c13c57c1ff84699b3e3c73905ad507b4e1d7c12b5b04e9296929fcc`. Files are in `artifacts/linux-hardware/`; this result supersedes the local builds. The log contains 24 warnings, including inherited vendor/compiler and linker warnings; no clock-skew or unresolved-symbol failure remains.

Ten comparisons of the compiled DT memory/GPU properties against actual live property bytes pass. There is exactly one RAM node, the selected reserved regions match, and no charging opt-in property exists. See `evidence/compiled-dt-verification.json`. A measured complete boot image has not been packaged; the raw kernel+DTB size alone does not establish boot-partition fit.

`patches/0003-asus-power-board-services-legacy-gpu.patch` contains 19 source changes relative to the preceding hardware spike. It applies after that spike's `0001-build-compatibility.patch` and `0002-asus-board-panel-touch.patch`. All 19 changed files replay exactly; hashes are in `evidence/patch-manifest.json`. This replay verifies the changes, not the Mac's unmodified case-colliding files.

## Builder and next gates

The user authorized GCP provisioning. VM/disk `PROJECT_REDACTED` in `PROJECT_REDACTED/us-central1-a` have 16 x86-64 vCPUs, 64 GiB RAM and a 600 GiB balanced disk. Both carry `experiment=asus-p00a-android17` and other teardown labels. The VM stops after 12 hours per run. Inventory, cost estimate and cleanup are in `infrastructure/README.md`. Disk charges continue after stopping.

The pinned LineageOS 24 / Android 17 source checkout completed after installing the missing Git LFS dependency. All **1,239 projects** are pinned to commit hashes in `infrastructure/resolved-lineage24-manifest.xml`; its hash is recorded in `evidence/platform-source-lock.json`. A separate sibling spike, `2026-11-05-asus-android17-kernel-backports`, investigates modern kernel features without mutating this hardware candidate. A reference kernel was cloned at a668db21f3cfddc5b73f081c6bb532b1b3351b36.

Still required: real Android 17 BPF/filesystem/memory features and tests; ASUS product/HAL integration; measured boot packaging; exact-unit backups and a demonstrated unsigned-boot/restore path. There is no Android 17 ROM or flash-ready image yet. A full kernel link alone does not clear those gates.

Transport and on-demand-root blockers are now cleared by the later audits. The live locked bootloader still forbids standard temporary boot, unlock ability is zero, and no failed-boot restore route has been demonstrated. Do not modify bootloader security state or flash based on the successful build results. All 4.9 hardware remains untested and diagnostic charging stays inhibited.

The generic mini_arm64 kernel-variable failure was cleared by the actual ASUS product. Its Android 17 init/ADB APEX and separate actual-kernel header export passed; see the device-product checkpoint for 24 locally verified files and provenance. No ROM has booted.

The builder's labeled disk is retained. VM stop status for this continuation is recorded in ../2026-11-05-asus-android17-device-product/evidence/vm-stopped.json. Storage charges continue after compute stops. Resource ledger and teardown remain in infrastructure/README.md.
