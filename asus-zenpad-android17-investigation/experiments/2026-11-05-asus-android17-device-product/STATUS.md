# Current continuation — 6 November 2026, 15:29 UTC

Goal ACTIVE. Parent coordinates Astra workers and alone controls physical operations.

15:38UTC: explicit recovery inverse also runtime-proven by no-reboot roundtrip: parent installed/verified control then actually wrote/verified original stock recovery, cleanup/Enforcing healthy. See orchestration evidence/explicit-recovery-inverse-runtime-20261106.json. User confirms no apps/files needkeeping: plan cleaninternal/data migration, no microSD/fullpersonalbackup gate. No userdata formatting yet.

The stock-kernel changed-ramdisk recovery control physically executed under locked
LK, showed the expected Red State warning, exposed authenticated report-only ADB,
and returned automatically to stock Android. Saved last_kmsg confirms deadline
service at uptime2.466 and recovery reboot syscall at131.255. The report read
failed errno13, so its report payload is unproved. Stock Android automatically
restored recovery; parent tool read back the complete 16,740,352 bytes matching
both original backups and verified fresh root, cleanup, SDK24 bootcomplete and
SELinux Enforcing. No new4.9-kernel or Android17 image has been flashed.
See ../2026-11-06-asus-android17-orchestration/evidence/stock-control-runtime-20261106.json.

Graphics r7 genuinely passed34strictELF/19linkerconfig checks and49checkpoint
hashes. r4 full product and exact signed Google sources are deployed on the
renewed labeled GCP builder. Full-build-r1 exited1 before compilation: lunch's
preliminary release-config query temporarily uses eng and trips the product's
eng rejection. Dedicated full-build Astra owns fixing this phase and integrating
checked SOC/Health patches, fresh ARM64 kernel and complete SDK37 images. It must
preserve authenticatedADB and charging inhibition, and clear stale installed
vendor files with installclean once. Separate Astra owns radio port and isolated
Linux target build; another owns diagnostic read repair and OS rescue transport.

Remaining physical gates: new4.9 kernel, full Android17 image fit/MTK packaging,
main-boot acceptance, independently usable recovery-side stockOS restore, data
medium and hardware/Play validation. Fresh read-only storage audit finds no
microSD card; stock/data is encrypted ext4 via dm-0. Physical system p25 geometry
and read-only mount match known GPT. Full stock system backup remains absent;
host has approximately1.3GiB free, so backup needs bounded authenticated streaming
or separate storage. Do not format stock/data or upload userdata/calibration.

---

## Historical checkpoint (superseded by current continuation above)

# Current continuation — 6 November 2026, 13:52 UTC

Goal ACTIVE. Parent is orchestrating three explicitly requested gpt-6-astra
agents. Exclusive ownership and integration boundaries are documented in
../2026-11-06-asus-android17-orchestration/README.md. No image flashed.

14:10 UTC: full-product Astra source implementation completed; parent reran all
21 offline checks, reviewed it and froze17device-source files for integration.
Full compilation remains pending graphics handoff. Parent corrected AOSP/MTK
empty-second-address validation using real mkbootimg/kernel fixtures. Separate
first-boot-services task resolves the actual keystore/APEX startup dependency.

Boot-path Astra found exactLK recovery verification failures returned but
ignored by callers. Parent reviewed and reran the bounded evidence checker;
bothstock recovery hashes and p10 geometry verify. This supports a supervised
stock-kernel changed-ramdisk recovery control without unlocking. Actual custom
execution/return/restoration are still unproved; diagnostic candidate and a
reviewed recovery-only inverse procedure are required before hardware testing.

Verified: actual SDK 37 framework, SurfaceFlinger, static first-stage init,
libc/linker, networking, ASUS AIDL lights and memory shim compile. Actual
Android 17 libc/linker/toybox and fork/RNG run successfully on generic ARM64
4.9 under QEMU. This does not establish physical ASUS boot or working hardware.

Current graphics gate: r4 build and keep-going collection both ended without
success. Old blobs use private core ABI symbols omitted from vendor contracts;
actual core Bionic/libsync contain most flagged symbols, while vendor Binder
really omits PermissionCache. Astra owns a coherent strict build fix, with
fresh input/log revisions and no global ELF-check bypass. Parent will review
its changes before full-product integration.

In parallel, Astra owns completing the staged full product init/mount/configfs
USB/memory configuration, and another owns an isolated diagnostic recovery
candidate with explicit stock rollback assumptions. Neither is authorized to
write to the tablet. Only the graphics agent mutates/builds on the VM until
that handoff is complete.

Parent prepared a full-image build supervisor and output validator in the
orchestration spike. It requires reviewed graphics completion/full deployment,
checks actual SDK37/static GPT settings, builds bootimage/systemimage, and
records hashes/layout without device access. The validator passed against the
real earlier MTK packaging artifact and rejected partition overflow and
malformed sparse fixtures. It has not been run against a full Android17 image.

Next delivery: integrate completed agents' source/evidence, deploy the reviewed
full product after the graphics job ends, and build actual boot/system images.
Then assess the controlled stock-kernel recovery test before testing 4.9.
Charging remains inhibited, gauge/HAL integration is incomplete, userdata is
FDE encrypted, and locked-LK custom-image acceptance is unknown. Preserve Play
services/Store as final-image requirements. Continue independent work across
ordinary build failures; stop only for a genuine impasse.

---


<!-- current-20261106 -->
Current checkpoint (6 November): SDK 37 init, device ADB APEX, exported kernel headers, netd, netbpfload and netd.o builds pass. All captured files verify. Image generation remains disabled; kernel APIs, HAL/policy integration, authorization and restore remain open. See the networking checkpoint below.

# ASUS Android 17 product checkpoint

5 November local / 6 November 2026 UTC. The actual ASUS P00A product compiles Android 17 init and the device ADB APEX. The separate real-kernel header export passes. No produced binary was installed on stock Android 7, and no flashable ROM or successful custom boot is claimed.

## Verified build

The resolved platform checkout remains pinned to 1,239 project revisions. The actual product exports the real kernel path and Lineage kernel variables, clearing the earlier generic mini_arm64 failure. Primary ARM64 and secondary ARM use ARMv8-A; the secondary Cortex-A53 combination requires armv8-a rather than armv7-a-neon. Shipping API is the actual original API 23. Effective platform SDK is 37, version-last-stable 17. The upstream trunk_staging codename label still says Baklava; the captured numeric SDK/source pins establish which source/API was built.

The initial product package list incorrectly named the apex-only device adbd as a platform PRODUCT_PACKAGES entry; the corrected product includes com.android.adbd. The successful build ran `m -j8 init com.android.adbd`, completed 14,150 executed steps, and finished in 24m15s including configuration/analysis. Both saved ELF files are AArch64/ELF64: init uses /system/bin/bootstrap/linker64, adbd uses /system/bin/linker64. APEX policy tests also passed. This is module/packaging validation, not hardware or old-kernel syscall compatibility validation.

A clean-platform control proved that the actual Lineage product excludes prebuilts/misc/protobuf_vendorcompat itself; the earlier generic-target protobuf patch was removed and remains removed. The pinned platform still requires three libjxl transitive dependency availability patches: libskia_skcms, libhwy, and XMP/MD5 vendor variants. The patches and actual source pins are captured. They do not implement device HALs or change kernel requirements.

The separate lineage_generator header output has no `m generated_kernel_includes` module alias; that first invocation failed with unknown target. Building its actual .dummy_dep output in the already validated ASUS aggregate Ninja graph succeeded, executing the real `headers_install` and Lineage clean_headers on the pinned ASUS kernel source. The standalone init/adbd build alone did not prove this header stage; the separate header test does. The kernel worktree stayed clean at `5ab69989839edfa650ed28876f2128e6ed467b9d`.

## Saved artifacts

All 24 files in artifacts/result/manifest.json pass their recorded size/SHA-256 checks after transfer to the Mac. The checkpoint includes actual binaries, compressed ADB APEX, generated real-kernel headers, device configuration, successful/failing build logs, effective SDK and source provenance, and the three retained platform patches.

- `android17-p00a-init`: 2,628,192 bytes; SHA-256 `3bf6dfd7d72361cbca869e36c13801e5a7a5829a478a529037a7d5c24c0633f2`.
- `android17-p00a-adbd`: 2,655,832 bytes; SHA-256 `28aa19919941d1a6e11b853e98f4a82eb9066c2650753c7a8ad5eed2906ecba1`.
- `com.android.adbd.capex`: 6,123,520 bytes; SHA-256 `ef9ffc28b94dc18e520f503d46ff099e7ef2e9fa366906b6d54bc2e7da6eea47`.
- `generated-kernel-headers.tar.gz`: 1,141,536 bytes; SHA-256 `09fa9f6fe3db9cea4f23c7eeb91c21ea5cacc3b78636eaf18d4b772b72baa7ac`.

## Reproduce/continue

The source lives on the labeled GCP Linux builder; see the sibling power spike infrastructure ledger. The Mac is case-insensitive and must not become the kernel build source. Product deployment creates an independent worktree from the already verified kernel source. The preparation script is one-shot and must not overwrite an existing product. `build_product.sh` verifies the actual device/kernel/API settings and disabled image-generation flags before compiling. `build_headers.sh` consumes its existing product Ninja graph; run it after the product build. `capture_product.py` records actual outputs and pins. The inputs tar was regenerated after the ARMv8/APEX fixes.

Boot/recovery/system/vendor/product/system_ext/userdata/vbmeta image generation is disabled in device.mk. Board partition sizes are from this exact live GPT, not the mismatching ZIP scatter. Full MTK boot packaging, first-stage fstab, legacy HAL/bionic compatibility, device SELinux policy, modern BPF/memory/syscall work, graphics and all new-kernel hardware tests remain outstanding. The diagnostic 4.9 DT still inhibits charging.

The sibling boot-access and root/hardware spikes cleared transport, exact-unit backup access and on-demand stock root. Boot, recovery, LK, both preloaders/boot areas and calibration-area backups exist; root block reads independently confirm boot/recovery/LK, and both raw GPT copies pass CRC checks. The locked bootloader still forbids standard temporary boot, unlock ability is zero, the ASUS key/seccfg path is unvalidated, and a failed-boot restore path has not been demonstrated. Do not flash or modify bootloader security data on the strength of the successful userspace build.

VM checkpoint: `PROJECT_REDACTED` is confirmed TERMINATED after local artifact verification. The labeled 600 GiB disk is retained for continuation; storage charges continue. Exact status/time/labels are saved in evidence/vm-stopped.json.

Recovery-access update: the BROM-recovery-proof spike established a preloader READY -> FASTBOOT mode request, independently verified the exact serial and status replies, and returned to healthy stock Android. Secure=yes, unlocked=no and unlock_ability=0 are unchanged. This clears entry to fastboot without working Android, but not BROM/DA storage access, image authorization or a failed-boot restore path. See its verified roundtrip JSON and STATUS.md. No image was sent or flashed.
# 6 November: networking module build checkpoint

The genuine ASUS SDK 37 / Android 17 product now also builds `netd`,
`netbpfload` and `netd.o` successfully, using scripts/build_network.sh. All image
generation remains disabled, and no output was installed on Android 7.

The checkpoint archive SHA-256 is
`43b2c7e92ef300dbdbc9ecdc54450aae86e9d23d63955069cc7a77a970accc6c`.
All 11 captured files verify after transfer to the Mac. Binaries are in
artifacts/network-result, with the manifest and source provenance beside them:

* netd: 584704 bytes, SHA-256
  `59a0eff453f713f4057a52598d0cf2ca1bd5ec5a09a77744e0f4ed9ea603b5ba`.
* netbpfload (APEX API 31 variant): 73720 bytes, SHA-256
  `41c17ce4333023be38732a75823fe30a4ebd52846a877e054420a7b4afdb90ff`.
* netd.o (EM_BPF object): 476832 bytes, SHA-256
  `c5232afa1ae316a42008983b99aec58332a073dd95a57a63a6033fe96763c2bc`.

The pinned Connectivity revision is
`7c04d866538e6f689823b769fb5c1e614ca0e295`. Its KernelUtils.h makes 5.10
the compile-time minimum for SDK 37 platform code; NetBpfLoad also rejects old
kernels by runtime release, including a later conditional 26Q4 floor of 5.15.
Our 4.9 kernel fails the unmodified SDK 37 requirement. BPF program/map ID APIs,
introspection and more are absent. Setting ro.bpf.kver_override is not a tested
solution. See the kernel-backport capability audit for the concrete gaps.

This is a module build checkpoint, not a complete networking APEX, installed
product, running Android 17 network stack or flashable ROM. The separate virtual
kernel experiment tests generic BPF behavior without risking the ASUS. Hardware
drivers, policy/HAL integration, image authorization and restore remain open.

# Framework/runtime build in progress

scripts/build_framework.sh now builds framework-minus-apex, services,
app_process and surfaceflinger for the existing SDK 37 ASUS product. It verifies
device/architecture/version and all eight disabled image-generation flags first.
No image targets were enabled and no output was installed on the ASUS.

The VM job started 2026-11-06 06:12:45 UTC with supervisor PID 148383 under
timeout 7200. Log: /srv/android/asus-device-product/logs/framework-build.log.
The shell trap records framework-build-exit-status; a successful build also
writes framework-build-complete. Process state and output, not these instructions,
are authoritative. Do not infer success before that evidence exists.

