<!-- current-20261106 -->
Current checkpoint (6 November): EROFS and the isolated networking-configuration kernel both build. Android 17 network modules compile, generic BPF runs in QEMU, and the first ID API adaptation is under virtual test. No Android 17 ROM or ASUS hardware boot is established. See the 6 November networking checkpoint below.

# Android 17 feature-port checkpoint

5 November 2026. The EROFS-enabled ASUS 4.9 kernel compiles and links on the GCP Linux builder. This is a feature candidate, not an Android 17 ROM. Hardware behavior, EROFS mounting and Google APEX installation remain untested.

## Verified outputs

`artifacts/linux-erofs/ASUS-P00A-EROFS-UNTESTED.Image.gz-dtb` is 7,231,738 bytes; SHA-256 `efaad28e8cbc51863de03049dc46c821afc624aa51bfe2556e5c3dc33c5310ec`. The compiled DTB has the same SHA-256 as the clean hardware baseline: `577a1ca5fbfe646ca02a50c190ac60efab0edd73c77c904a33865859e2d87bfc`. Charging remains inhibited. The full boot image (header, wrappers, ramdisk and padding) has not been packaged or measured.

All 41 captured checkpoint files pass their saved size/hash manifest. The combined feature patch applies cleanly to the independently built hardware source. The hardware baseline itself is reconstructed from the pinned original archive plus three ASUS patches, preserving all 12 case-colliding source groups on Linux. The Mac source snapshot is for editing/reference, not a complete build source distribution.

## EROFS integration

Reference: anton-scholten/android_kernel_samsung_sdm670 at a668db21f3cfddc5b73f081c6bb532b1b3351b36. Its EROFS import/update/fixes were applied to a separate copy of the ASUS hardware source. Samsung device definitions/configurations were not imported. Ten local source commits cover the prerequisite, import/fixes and MT8163 adaptations; `source-history.txt` and the original/adapted patches preserve provenance.

The first prerequisite patch failed because this MT8163 baseline lacks the atomic conditional-read acquire wrappers already present in the donor. The adaptation supplies the same upstream wrappers over the existing ordering primitives and adds their relaxed forms. The first compile then caught the donor's incompatible three-argument getattr adaptation; MT8163 already uses the four-argument form, so that implementation/prototype was restored. A second compile caught the older kstat representation: attributes exists, attributes_mask does not; the adaptation retains the supported attributes. The baseline statx result code clears the reserved field at the modern mask offset. This is not a claim of fully current statx behavior; runtime/API tests remain necessary.

Enabled: EROFS, xattrs, POSIX ACL, security labels, compressed data and ARMv8 LZ4 acceleration. Compile/link passes after the adaptations, with inherited warnings retained. No feature capability was inferred solely from changing a kernel version property.

## Platform continuation

The actual ASUS product follow-up now builds SDK 37 / Android 17 init and the device ADB APEX successfully. Its separate real-kernel header export also passed. All 24 captured checkpoint files verify after transfer to the Mac. See `../2026-11-05-asus-android17-device-product/STATUS.md` for exact hashes, product configuration, source pins, retained platform patches and reproduction scripts. No binary was installed on Android 7 and no bootable ROM is claimed.

The original mini_arm64 control failure was a missing Lineage product/kernel-variable export, not proof that Android 17 userspace cannot compile. The ASUS product clears it. Its Lineage source filter also makes the generic protobuf dedup patch unnecessary; that patch was removed. The three libjxl vendor-dependency availability patches remain required and are captured with the product checkpoint.

## Device continuation

The user confirmed that a five-second Power hold restarted the tablet. A bounded libusb client subsequently cleared the Mac fastboot transport obstacle, read actual secure/lock/partition replies, obtained two matching reads of sixteen areas and successfully rebooted to Android. Runtime replies are secure=yes, unlocked=no and unlock_ability=0. Both 4 MiB boot areas contain the exact official preloader. The live LK matches the official binary used for static analysis. See the sibling boot-access-audit STATUS.md.

The user then explicitly authorized root and hardware validation. On-demand UID 0 root is demonstrated on stock WW 5.3.20 and SELinux is restored to Enforcing after root sessions. Independent Linux-block reads of boot/recovery/LK match the fastboot reads. Both raw GPT copies pass CRC checks and all 26 entries match the live map. Stock Wi-Fi internet/DNS and Bluetooth discovery work; charging diagnostics are normal. Physical touchscreen coverage, Bluetooth pairing/audio and all new-kernel hardware behavior remain unproved. See `../2026-11-05-asus-root-hardware-validation/STATUS.md`.

## Remaining gate

The exact live LK forbids its standard temporary boot handler while locked. Root does not unlock it. The ASUS per-device key/security-config route and failed-boot restore path remain unvalidated, and full system/userdata backups are still absent. Stock kexec interface/implementation discovery has not established an alternative RAM boot path. No unlock, wipe, bootloader-security modification, custom boot or flash was performed.

The rest of the donor's roughly 2,400+ feature commits has not been applied. Modern BPF/memory/syscall functionality, old HAL/bionic integration, device SELinux policy, complete MTK boot packaging and hardware validation remain. Charging is deliberately inhibited in the diagnostic 4.9 DT. Successful EROFS/kernel/userspace builds do not clear these runtime requirements.

Keep the tablet in Android. Continue from pinned Linux sources, not the case-collapsed Mac kernel tree. The labeled GCP disk retains the source and build outputs; VM stop status is recorded in the product checkpoint evidence. Do not flash without a validated boot/restore plan.
# 6 November: networking configuration candidate

An isolated Linux worktree (`/srv/android/asus-android17/kernel-network`) at
`de61780979adc3c52068e244aa62ae0369c00527` adds four existing configuration
options to the verified EROFS/hardware source: BPF_JIT, NET_CLS_BPF,
NET_CLS_MATCHALL and NET_ACT_BPF. The baseline source/worktree and earlier images
remain unchanged. Reproduction: scripts/prepare_network_config.py and
scripts/build_network_kernel.sh.

The full Image.gz-dtb build passes. The local candidate
artifacts/linux-network/ASUS-P00A-NETWORK-CONFIG-UNTESTED.Image.gz-dtb is
7240835 bytes, SHA-256
`677764d872c87ab53081a99ace7c6fff00493b6215d6695f476ae31bc455bde6`.
Its DTB still hashes to
`577a1ca5fbfe646ca02a50c190ac60efab0edd73c77c904a33865859e2d87bfc`;
charging remains inhibited. All ten captured metadata/config/log/patch files
verify after transfer. The Linux source patch is also retained in
artifacts/linux-network/network-result/network.patch.

The before/after reports from scripts/audit_network_requirements.py identify
configuration versus API gaps. BPF_JIT_ALWAYS_ON is implemented in init/Kconfig
but remains disabled in this candidate (it was hidden from the old config while
JIT was off). Do not mistake a missing .config line for missing source support.
Program/map ID enumeration, GET_FD_BY_ID, OBJ_GET_INFO_BY_FD, PROG_QUERY,
BTF_LOAD, MAP_FREEZE and LINK_CREATE declarations are absent; the pinned donor
contains them. Static header declarations alone would not prove implementation
or successful verifier execution.

Android 17 netd, netbpfload and netd.o now compile in the real ASUS product. The
unmodified SDK 37 networking platform still requires kernel 5.10; later 26Q4 code
has a conditional 5.15 gate. Neither four configuration changes nor a version
override clears those requirements. Next: test the generic BPF code virtually,
then port bounded feature groups with runtime/API checks. No custom image has
been booted on the ASUS or flashed.

# First BPF API group: virtual tests passed

The original donor's program-ID patch fails an index-only application check on
this older baseline. scripts/prepare_bpf_ids.py explicitly adapts program/map ID
lifetime handling and GET_NEXT_ID from three pinned donor commits. The virtual
feature revision is `34a8afba47785b0ff9dc2a72dade73c945a54a55`.

The isolated ARM64 QEMU tests pass enumeration, end-of-list, invalid starts,
unprivileged denial (with MULTIUSER enabled), map/program FD-allocation failure,
absence of leaked IDs and final reference release. Basic map read/write and a
real socket-filter execution also pass. The VM exits cleanly through poweroff.
This clears those two ID-enumeration API gaps virtually, not on ASUS hardware.
GET_FD_BY_ID, object information and the rest of the modern BPF stack remain.

The exact patch and all 20 virtual checkpoint files verify locally under
../2026-11-06-asus-kernel-virtual-validation/artifacts/ids-result. The separate
hardware configuration rebuild passes at /srv/android/asus-android17/
kernel-bpf-ids and build-bpf-ids, source revision
`790faa7607c819a5d61425283cb4784bc413b735`. It applies only the BPF patch;
the generic GIC test fix is not imported. The earlier hardware sources/artifacts
stay unchanged.

The new kernel-only image is 7240481 bytes, SHA-256
`2be9f759041e4baa7af0f43ba0c800769f922b24443a811747db80e90bf54af4`.
DTB is still the verified hardware baseline hash; charging is still inhibited.
All 12 files in artifacts/linux-bpf-ids/bpf-ids-result verify after transfer. The
compiled configuration matches the network baseline byte-for-byte; three BPF
core source files match the virtual-tested files exactly. GET_NEXT_ID appears in
the linked System.map. None of this is an ASUS runtime or Android 17 boot pass.

# Lookup-by-ID API group: virtual tests and ASUS build passed

scripts/prepare_bpf_fd.py and fix_bpf_fd_access.py preserve the original failed
adaptation and final correction. Final virtual revision is
fcb1b6c2de6348e2724981dcd520dec631ed5255; hardware revision is
717bb3c9e13ce573cfdd2dda856debd27a0fa17f. The final map-FD constructor uses
O_RDWR, and both creation/lookup failure paths drop map user references as well
as object references. These include the donor's later stable fixes.

The virtual tests pass real looked-up-map writes/reads, program execution,
permissions, malformed queries, FD failures, captured publication/failure races,
program-array user-reference cleanup and final release. The old ID/basic tests
remain green. The VM exits through poweroff with no timeout. Full logs and the
first failed run are retained; all 31 virtual archive files verify on the Mac.

The separate ASUS build passes. Its kernel-only image is 7242232 bytes, SHA-256
`7c7051c147b03ca865b3481d55cd832bc6f2732eef1c0063af9404823b0ceaa4`.
All 12 files in artifacts/linux-bpf-fd/bpf-fd-result verify. Compiled config
matches the ID candidate byte-for-byte. The BPF core files match the virtual
tested files; the hardware GIC source is unchanged. ARM64 Image magic and exact
appended DTB were inspected after transfer. DTB is still the original diagnostic
hash, and charging is still inhibited. This is not a boot.img or a ROM, and has
never booted on the ASUS.

The Android 17 framework/runtime build is ongoing on the existing VM. Next BPF
group is object information, including real tag and JIT-length prerequisites.
The SDK 37 networking requirement remains unresolved; no version override was
set and no flash/reboot/device modification was performed this continuation.

