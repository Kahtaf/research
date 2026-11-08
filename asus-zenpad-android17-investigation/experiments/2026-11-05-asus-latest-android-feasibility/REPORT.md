# ASUS Z380M / P00A: newest Android feasibility audit

> Follow-up correction, 5 November 2026: the recursive live-DT pull contained zero files; its decoded output was an empty root node, not a recovered live device tree. The official boot DTB is valid. Direct live property reads in the subsequent kernel bring-up identify the panel as `z380m_kd_rm68200g01`, touch as GT6108, charger as BQ25896, gauge as UG31xx and backlight as LP8557. The first full compile also finds the pinned `lineage-22.2` kernel incomplete: it references missing `linux/refcount.h` in its BPF backport. Treat that revision as a backport reference, not a buildable foundation. The bring-up is testing the same repository's pre-backport 4.9.337 revision `dc63af1741072236efb511499f1f0b9dd281d694` instead. Android 17 remains the target. The follow-up has now recovered all 2,075 live properties correctly and built the 4.9 control kernel; the ASUS port reaches final linking and fails at the unported charger interface. See the sibling `2026-11-05-asus-mt8163-kernel-bringup/STATUS.md` for build results.

Audit date: 5 November 2026. **Verdict: proceed with an experimental Android 17 / LineageOS 24 port, subject to recovery and hardware gates. There is no demonstrated Android 17 image for this ASUS.** The first engineering candidate should be an MT8163 4.9 kernel with ASUS board support, followed by modern Android kernel backports and legacy vendor integration. Mainline Linux is a second candidate if the old graphics stack proves unusable.

This is a research go decision, not a claim that the port will succeed. The audit collected device evidence, recovered the exact official boot payload, inspected source and vendor binaries, and ran bounded build probes. It did not root, unlock, reboot, wipe, or flash the tablet. No bootable custom ROM was produced. Existing Google packages and the debloat state were left untouched.

## Target and practical result

**Android 17, API 37, using LineageOS `lineage-24.0`, is the target.** Google's [current release documentation](https://source.android.com/docs/setup/start/requirements) identifies `android17-release`; its [build table](https://source.android.com/docs/setup/reference/build-numbers) lists Android 17 and the public `android-17.0.0_r1` tag, alongside separate security tags. Individual AOSP files from that release and the LineageOS 24 manifest were retrieved successfully in `sources/android17/`. Before a full build, freeze the complete resolved manifest and review current security updates. A moving branch or a version string alone is insufficient provenance.

Android 11/LineageOS 18.1 MT8163 work is useful for driver and device-tree comparisons. It is not the proposed end product. A short diagnostic boot of an older userspace could isolate a driver problem without changing the Android 17 objective.

Proposed success means: Android 17 reaches the launcher, hardware acceleration and touch work, Wi-Fi connects, charging and thermal control remain correct, suspend/resume works, and Play Store/Play services operate. Cameras and Bluetooth can follow the first interactive boot. Passing a version-property check does not meet this definition.

## What the actual tablet establishes

| Item | Observed evidence | Consequence |
|---|---|---|
| Board | ASUS P00A / P00A_2, MT8163, four Cortex-A53 cores, 64-bit kernel and userspace | ARM64 CPU architecture is suitable; platform integration is the harder problem. |
| Memory / display | Approximately 2 GB RAM, 800 × 1280 display | Start with a lean product and measure memory pressure. No performance claim yet. |
| Current software | ASUS WW 5.3.20, Android 7.0, June 2018 patch level | Vendor components predate Treble. |
| Kernel | 3.18.35, GCC 4.9; same version recovered from the downloaded matching official boot image | Retaining this kernel for Android 17 would require a much larger compatibility effort. |
| GPU | Mali-T720; proprietary driver advertises GLES 3.1 | Potential reuse, but its Android 7 dependencies must be resolved. |
| Touch | Running input device is Goodix; stock DT includes `goodix,gt6108` | Preserve this board's configuration; do not substitute a Fire tablet DT. |
| Vendor interfaces | Old `/dev/binder`, ashmem and ION; no mounted BPF filesystem, hwbinder/vndbinder nodes or DRM directory observed | Missing runtime nodes do not prove source lacks features; modern interfaces must be enabled, implemented and tested. |
| Partition layout | boot and recovery each 16,740,352 bytes; system 3,753,902,080 bytes; userdata 11,331,268,096 bytes | Strict image budgets. No separate vendor or super partition in the live map. |
| Boot / root | ADB is UID 2000, no `su` on PATH, verified boot green, SELinux enforcing | No root access demonstrated; bootloader unlockability and unsigned boot are still unproven. Green state alone is not a complete unlock test. |
| Build host | Apple Silicon Mac, 16 GB RAM; Docker VM about 8 GB RAM; free host disk fell from about 41 GiB to 33 GiB during audit | Suitable for these probes, not a full local modern Android checkout/build. |

Raw results: `evidence/device/collection.json`, `evidence/device/final-readonly-check.txt`, `evidence/live-partition-layout.json`, `evidence/stock-boot-unpack.json` and `evidence/vendor-abi.json`. Device identifiers appear in local evidence; it is not a public release bundle.

## Sources recovered, and what they do not prove

1. **Original ASUS GPL archive recovered.** [Kernel_V4_7_0.zip](https://dlcdnets.asus.com/pub/ASUS/EeePAD/Zenpad/Z380M/Kernel_V4_7_0.zip) contains the core kernel directories absent from the [Vosjedev GitHub copy](https://github.com/Vosjedev/linux-asus-p00a-kernel/tree/a724060f193a31e0bd7311d446400aece5298f99). That copy is useful for finding ASUS drivers, but its missing core directories prevent a standalone build. The original archive includes Linux 3.18.22, board DTS files, MediaTek/ASUS drivers and GCC 4.9 toolchains. It is older than the installed 3.18.35 kernel. Its product-specific `vendor/asus/bsp/<project>/<project>_diffconfig` is absent. The supplied base configuration therefore cannot be called the exact shipping configuration.
2. **Matching official firmware recovered.** [UL-P00A_2-WW-5.3.20.0-user.zip](https://dlcdnets.asus.com/pub/ASUS/EeePAD/Zenpad/Z380M/UL-P00A_2-WW-5.3.20.0-user.zip) yielded boot.img, init/fstab files, the 3.18.35 kernel and appended device tree. The live device tree was also pulled and decoded. No embedded kernel config was found; `/proc/config.gz` is unavailable. The OTA is not a complete backup of this unit and contains no recovery.img.
3. **Same-SoC Android kernel candidate exists.** [amazon-oss MT8163 `lineage-22.2`](https://github.com/amazon-oss/android_kernel_amazon_mt8163/tree/a81e526957ef342c4ea0c7ff5a3e95366427d0cd) is Linux 4.9.337. It offers a more useful modern Android starting point than 3.18, but does not provide an ASUS Z380M board port. The common device tree examined only has branches through 18.1. The apparent `lineage-24.0` local manifest is for **MT8188 / Fire Max 11 sunstone**, not MT8163; it was ruled out as direct support.
4. **A modern Linux MT8163 development tree exists.** [bengris32 `mt8163/7.0`](https://github.com/bengris32/linux-mtk/tree/20951722df6ae1f6fecbfcea0a7d585118a06f3f) identifies itself as 7.0-rc6 and contains MT8163 GPU, display and other SoC nodes. These are development patches, not proof that all hardware works. The targeted MediaTek DT directory contains Amazon boards but no ASUS P00A/Z380M board. Some board examples, including biscuit, use `mt8163-headless.dtsi`, disabling GPU, display blocks, IOMMU and thermal nodes. Others do more: the common Amazon DT enables the GPU and rook wires a DSI panel. Thus headless support is not the limit of this development tree, but none of these descriptions establishes ASUS display operation. A generic Panfrost match does not establish a working ASUS screen.
5. **Same-device Linux boot evidence exists.** [kaantcp/z380m-alpine](https://github.com/kaantcp/z380m-alpine/tree/7218a276f252a59874ab860683c061fa2b856519) reports Alpine running with the stock ASUS kernel, framebuffer and touch. It reports no Wi-Fi and an incompletely documented local mtkclient patch. This is useful boot packaging evidence; it neither demonstrates a new kernel nor proves the same access path on our unit.

Archives are retained with SHA-256 checksums. The ASUS source archive hash is `d8b9d77a7e8b5151c2b68c96e784842a25b167cf8a7044188e7044a5fdbcd41c`; the firmware ZIP hash is `eea443c205596106f041f1054fcbed0158c6c7986b899b9545d84fcd9d38a81c`. GitHub metadata, commit IDs, downloaded port patches and provenance are under `evidence/upstream/`, `sources/reference/` and `sources/ports/`.

## The important Android 17 precedent

The [Galaxy Tab S5e port](https://github.com/anton-scholten/lineageos-galaxy-tab-s5e/tree/a3f069b003c490373cd6f3d5317e4dcda2ab881e) reports working Android 17 / LineageOS 24 on a 4.9 kernel. Its actual manifests and kernel source were inspected, not only its headline. The author describes roughly 2,450 kernel backport commits plus device/platform compatibility changes. This establishes a credible technique, not transferable Samsung hardware support or independent verification of the claimed runtime behavior.

Its [port notes](https://github.com/anton-scholten/lineageos-galaxy-tab-s5e/blob/a3f069b003c490373cd6f3d5317e4dcda2ab881e/UPSTREAM.md) identify eBPF, memory-management, FUSE, encryption and EROFS work. EROFS matters here: the reported Google Play services APEX required it. Modern Google support needs to be a kernel/filesystem acceptance test, not an APK installation afterthought. The referenced kernel was pinned at `a668db21f3cfddc5b73f081c6bb532b1b3351b36`; files inspected include its Makefile, BPF UAPI and EROFS implementation.

A [Redmi 9A Android 17 project](https://github.com/qcom-toolbox/EVOLUTION-X-DANDELION-17/tree/75f316ebd586d93e98fb912a273a33e8845dc3d7) reports a boot using a MediaTek 4.9 kernel and Android 10 vendor. Its patches address BPF, libc, old HALs, VNDK and missing vendor partitions. This is a secondary compatibility reference: its SoC/GPU differ, vendor baseline is newer, and the demonstrated build is vanilla without Google apps. Copying its platform bypasses would not establish feature completeness or security on ASUS.

The inspected LineageOS 24 connectivity loader still includes kernel-version-specific behavior, rather than a simple universal compile-time minimum. Google's [supported Android kernel matrix](https://source.android.com/docs/core/architecture/kernel/android-common) describes supported/tested combinations. It does not prove that a custom 4.9 port is impossible, nor certify one as supported.

## Build experiments actually run

| Probe | Result | Interpretation |
|---|---|---|
| Original ASUS product `make ..._defconfig` | Failed | Custom ASUS make rule references missing product diffconfig; initial unset Android build paths also fail. |
| Supplied base defconfig → `olddefconfig` | Passed | Kconfig can resolve a useful source baseline. It is not the exact shipped config. |
| Kernel `prepare` with GCC 13 | Failed: `compiler-gcc13.h` missing | Expected old-source/new-toolchain incompatibility; not a hardware impossibility. |
| Original ASUS GCC 4.9 under Linux amd64 emulation | Toolchain runs; `olddefconfig` and `prepare` passed | Generated kernel headers and ARM64 bounds/offset compilation work with the period toolchain. Full kernel linking and boot are untested. |
| ASUS Z380M DTS preprocessor + dtc | Passed with legacy binding warnings | Board description is recoverable and compiles. No boot validation. |
| Exact official boot extraction | Passed | MTK 512-byte wrappers, gzip kernel, appended DTB and ramdisk recovered; Linux version matches running tablet. |
| Live DT pull / decode | Passed | Gives this unit's runtime board description for comparisons. |
| Vendor ELF inspection | 486 ELF files found, 16 key samples inspected | GPU/composer/audio/camera/sensors exist in both ABIs. No vendor executable was run on the host. |

Build commands and logs are in `scripts/build_probe.py`, `scripts/legacy_prepare.sh`, `Dockerfile`, and `evidence/build/`. These are evidence probes; generated DTBs are not installation images.

## What stands between us and Android 17

**ASUS hardware on 4.9.** Bring over the actual panel initialization/power sequencing, Goodix touch, PMIC/regulators, charger/fuel gauge, eMMC, USB and MediaTek connectivity support. Recover the selected panel variant from stock driver/boot evidence; a generic `mediatek,lcm` node does not identify it conclusively. A kernel that boots over USB but cannot charge correctly or keep temperatures controlled is not a usable milestone.

**Graphics and old vendor ABI.** The 64-bit Mali library depends on 14 shared libraries; the composer on 23, including Android/MediaTek UI extensions. They import old C++ interfaces such as GraphicBufferUtil and GuiExtClientConsumer. Copying them into Android 17 is not sufficient. Need an explicit linker dependency closure, compatible userspace libraries/shims, legacy gralloc/composer wrappers and a matching Mali kernel UAPI. This audit did not compare every imported symbol against a complete Android 17 build, so the precise shim set is still unknown.

**Mainline graphics is also work.** [Mesa documents Mali-T720 Panfrost](https://docs.mesa3d.org/drivers/panfrost.html) as GLES 2.0/OpenGL 2.1 with no Vulkan support. That is below the stock driver's advertised GLES 3.1. Panfrost also needs working DRM/display, power, clocks, memory and board wiring. For Android 17, test the selected rendering backend explicitly; software rendering can diagnose a first UI but is not evidence of acceptable interactive performance. Lack of Vulkan alone is not a proof that no custom Android UI can boot.

**Modern kernel facilities.** Backport and test actual BPF behavior, binder interfaces, memory/cgroup features, modern syscall fallbacks, filesystems/APEX support and encryption requirements. Setting a fake kernel-version property is not implementation. Preserve 4 KiB page compatibility for existing blobs unless proven otherwise; do not assume this retrofit must use a new device's launch configuration.

**Storage and Google apps.** Keep the existing partition table for initial experiments. Use a compact system/vendor layout supported by the product, and measure generated image sizes against exact live partition sizes. There is no off-the-shelf GSI installation path on this non-Treble stock system. APEX/EROFS, Google setup, WebView, Play Store, updates and background memory use need device tests. Google certification/Play Integrity are not guaranteed by a functional port.

**Recovery is unproven.** The bundled scatter offsets differ from live GPT/sysfs: for example system is at 549,081,088 bytes live, versus 192,937,984 in the file. Do not use that scatter as this unit's raw flash map. The correct firmware version does not turn a generic scatter into a device backup. We have not tested BROM access, DA authorization, bootloader unlock or `fastboot boot`. Do not assume any is available or bypassable from another model's exploit.

**Build resources.** Google's [current workstation guidance](https://source.android.com/docs/setup/start/requirements) calls for x86-64 Linux, 400 GB free storage and 64 GB RAM. Our Mac/Docker environment is below that supported setup. A full platform build should run on a suitable Linux builder; no paid/cloud resources were provisioned during this audit.

## Ranked routes

| Route | Role | Reason |
|---|---|---|
| MT8163 4.9 + ASUS drivers + Android 17 backports | **First candidate** | Same-SoC Android foundation and demonstrated 4.9-to-17 techniques elsewhere; strongest path toward retaining proprietary GLES support. ASUS bring-up and blob compatibility remain unproven. |
| Modern MT8163 mainline + Android 17 + Mesa | **Alternative research candidate** | Better long-term kernel direction, but ASUS board/display/power work and T720 graphics limits can dominate. Try if legacy graphics or 4.9 integration fails its gates. |
| Stock 3.18 + Android 17 platform bypasses | **Diagnostic only** | Maximizes old driver reuse while magnifying modern-kernel gaps. Not the recommended product foundation. |
| Another tablet's ROM/GSI | **No direct installation candidate** | Different board or non-Treble vendor integration; same SoC is not interchangeable firmware. |

These rankings are engineering judgments from the evidence, not measured success probabilities. No defensible completion date or performance estimate is available yet.

## Concrete continuation and stopping points

1. **Offline ASUS 4.9 bring-up spike.** Create a separate workspace spike. Pin the MT8163 4.9 tree above, import only identified ASUS board/drivers with provenance, and produce a driver/Kconfig dependency matrix. Build a minimal kernel and initramfs with USB diagnostics, storage, panel/touch and essential power protection. The old ASUS toolchain/config probe is a reference, not the toolchain to force onto all modern work. Pass: a complete linked kernel fits the existing boot budget and has reproducible logs. Stop before flashing if hardware power wiring or image layout is uncertain.
2. **Prove recovery on this exact unit before a custom boot.** Obtain verified read access to live GPT, boot, recovery, preloader/boot areas and device-specific NVRAM/protect/persist/ASUS calibration partitions. Keep an off-device manifest with sizes and hashes. Determine the actual unlock/unsigned-boot/BROM path from observed behavior, preserving stock preloader. A restore design must cover a device that no longer reaches Android; an ADB backup alone does not. A recovery test is a separate device-changing experiment, not performed in this audit. Stop if there is no credible restore path.
3. **Minimal hardware boot.** Prefer a temporary boot if the bootloader actually supports it; otherwise review the exact flash/restore plan first. Capture early console or persistent logs. Pass: USB diagnostics, storage, repeatable boot, charging/thermal protection and panel/touch work. Stop on power faults; do not stack Android troubleshooting on broken hardware.
4. **Android 17 kernel/platform bring-up.** On an adequate Linux builder, freeze LineageOS 24 source, port the relevant backport series feature by feature, and build an ASUS product with collected vendor files and explicit compatibility wrappers. First acceptance: init → ADB → SurfaceFlinger → system_server → launcher. Diagnose a stage with minimal userspace if needed; keep the final target 17. Pass BPF/filesystem/encryption tests rather than hiding failures with version overrides.
5. **Usable tablet and Google acceptance.** Validate acceleration, Wi-Fi, audio, suspend/resume, charger behavior, storage and reboot recovery. Then validate an Android 17-compatible minimal Google package set including EROFS/APEX mounts, setup, Play Store installs/updates and WebView. Preserve original Google components on the current stock system throughout development. Full Google functionality on the port is a completion condition, not established by this audit.
6. **Pivot gate.** If an ASUS 4.9 kernel is viable but proprietary graphics cannot be bridged, run a distinct mainline display/Panfrost experiment using the recovered panel/touch evidence. If neither route establishes a display and recoverable boot, report those failures and revisit scope. Do not present an older release as completion without an explicit change of objective.

Next useful engineering action: **build the ASUS-specific 4.9 kernel candidate offline while preserving Android 17 as the ROM target.** The current audit has enough evidence to justify that experiment, and not enough to justify flashing a borrowed image.

Current continuation: see the sibling boot-access-audit, root-hardware-validation and android17-device-product STATUS.md files. Fastboot transport and stock on-demand root now work; exact-unit critical-area/GPT backups are verified; the real ASUS SDK 37 init/ADB APEX and kernel-header builds pass. Locked-state unsigned boot/restore and 4.9 hardware runtime remain unresolved. Earlier audit statements describe the evidence available at that stage.
