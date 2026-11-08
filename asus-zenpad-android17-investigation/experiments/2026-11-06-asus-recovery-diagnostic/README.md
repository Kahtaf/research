# ASUS recovery diagnostic

Question: can a minimal RAM-only recovery image isolate locked-LK custom-image
acceptance from first boot of the ASUS 4.9 kernel?

Status: **offline artifacts complete; readiness to attempt a supervised
stock-kernel control: NO.** The present evidence does not establish return to
normal stock boot after a rejected/custom recovery, or re-establishment of
on-demand root after that return. Current device availability/preflight was not
checked because device commands are outside this task. These are concrete
restoration prerequisites, not a demand to prove image acceptance before testing
it. The images are useful controlled test inputs, not a flash-ready claim.

Only this new spike was written. No device commands, flashing, VM source/build
mutations, cloud changes, goal changes, or subagents were used. SSH was used for
source identity reads. All outputs, including superseded versions and local
compiler intermediates, occupy approximately **121 MiB**. No Android 17 userspace
is included: this experiment tests acceptance and kernel/early-userspace bringup.

Use **candidates-v3** only. v1 retained the stock header's permissive request;
v2 corrected that request but lacked the adbd launch guard. Both are superseded
and preserved rather than overwritten.

The two final images are:

- [Stock-kernel acceptance control](artifacts/candidates-v3/UNTESTED-stock-control.img),
  **8,652,800 bytes**, SHA-256
  `f8c950819af579946071465e969e8eff454b6f8422d5eb19b3adb9bcd382da90`.
  The entire wrapped kernel is identical to the verified stock recovery backup.
- [ASUS 4.9 hardware probe](artifacts/candidates-v3/UNTESTED-asus49-probe.img),
  **8,423,424 bytes**, SHA-256
  `34d74ee0a2728e5595fe443c84b31289ffc18acea4a09dc1ce9483c21fa87fa4`.
  The unwrapped kernel is the pinned BPF-FD artifact with SHA-256
  `7c7051c147b03ca865b3481d55cd832bc6f2732eef1c0063af9404823b0ceaa4`.

Both fit the actual **16,740,352-byte** recovery partition, leaving 8,087,552
and 8,316,928 bytes respectively. They are compact boot images, not full-partition
restore backups. Neither has a valid ASUS signature. The original trailer and
partition padding were removed rather than presented as valid authentication.
Locked LK acceptance remains an experiment outcome. Ordinary temporary
`fastboot boot` is not an available assumption on this locked unit.

Both images contain the identical 22-entry ramdisk: 3,010,048 bytes uncompressed;
wrapped SHA-256
`527c77f24bd33ec1b69845acd5032db3f1326937447486f05a110f91a2c65732`.
Kernel/ramdisk/tags addresses remain `0x40080000`, `0x44000000`, `0x4e000000`;
page size remains 2048. Header changes are payload sizes, Android SHA-1 ID, and
the specific replacement of `androidboot.selinux=permissive` with `enforcing`.
Full hashes, modes, contents, tool identities and input identities are in the
[manifest](artifacts/candidates-v3/manifest.json).

Actual implemented probe behavior, conditional on LK executing the image:

1. Trusted stock recovery `/init` loads the derived policy. The only init
   configuration is [source/init.rc](source/init.rc): no imports, fstab,
   `mount_all`, modules, charger, healthd, fuel-gauge daemon, recovery updater,
   graphics daemon, or Android framework. Stock boot ramdisk is not reused.
2. The early action requests enforcing mode and starts an independent deadline
   process, then stock ueventd. Init's standard `/dev`, devpts, proc and sysfs
   setup is inherited. Our rc mounts only a 1 MiB `nosuid,nodev,noexec` tmpfs at
   `/tmp`, configfs, and ADB FunctionFS. There are no eMMC filesystem mounts,
   `/data`, `/cache` or `/persist` mounts, block-device reads/writes in the
   helper, firmware-loading rules, or legacy module files. Ueventd may create
   block device nodes; that does not mount/open their contents.
3. The same rc attempts the stock legacy `android_usb` interface and the 4.9
   configfs interface. Missing legacy/configfs nodes may log errors on the
   other kernel. Only ADB is configured, using `0e8d:201c`. Configfs binds
   `musb-hdrc` after **adbd** publishes `sys.usb.ffs.ready=1`. The UDC name is
   source-backed, not hardware-confirmed. Configfs's USB serial is
   `P00A-DIAGNOSTIC`; legacy enumeration may retain the original serial.
4. The adbd service initially runs the bounded helper's `--adbd` guard, in the
   adbd domain. It requires `/sys/fs/selinux/enforce` to read `1` and the
   FunctionFS ep0 path to exist. Only then does it exec the fixed trusted
   `/sbin/adbd --device_banner=recovery`, preserving init's socket environment.
   It cannot accept an alternate executable or arguments. This prevents the
   reference adbd's no-USB TCP fallback on a failed FunctionFS setup. No
   networking is configured. On guard failure init can retry; the deadline
   continues independently.
5. Stock adbd is configured with `ro.secure=1`, `ro.adb.secure=1`,
   `ro.debuggable=0`; it is expected to drop to UID 2000 and require key
   authentication. The only command endpoint, installed as `/system/bin/sh`,
   accepts exactly `-c report`. It is **not a shell**: compound commands,
   paths, interactive sessions and reboot commands are rejected. Authenticated
   `adb shell report` prints `/tmp/diagnostic.txt`; `adb pull` of that file is
   also policy-permitted. No host command was executed against a device here.
6. A separate root recovery-domain invocation collects a single early snapshot
   into `/tmp/diagnostic.txt`: kernel/version/cmdline, uptime, memory, mounts,
   filesystem/partition listings, input descriptions, interrupts, SELinux
   state/context, framebuffer metadata, battery/USB uevents, USB state and
   bounded directory listings. A read-only kernel-ring request is attempted;
   denials are recorded. Each ordinary file is limited to 8 KiB, ring output to
   32 KiB, total report to 256 KiB; unavailable data records an error, not a
   successful hardware test. There are no framebuffer drawings, touch-event
   capture, charging changes, Wi-Fi bringup, or camera/audio tests. USB state
   may be captured before enumeration finishes.
7. The deadline uses an absolute monotonic deadline **120 seconds after its
   service starts**, then calls normal Linux `RESTART`, with no recovery target
   or BCB write. Interrupted sleeps cannot extend it; clock/sleep errors request
   an earlier reboot. Init restarts the deadline if the reboot syscall returns.
   `panic=15` and `panic_on_oops=1` are requested once the init action runs.
   This is a software deadline, not a hardware watchdog and not protection
   against a pre-init failure, scheduler hang, blocked reboot handler, or LK
   rejection. A hung report read does not block the separate deadline process.

The report is lost on reboot unless retrieved. RAM-only describes this ramdisk
and helper's filesystem behavior; it is not proof that LK or either kernel never
writes hardware reset state or crash diagnostics. Stock kernel power behavior
remains stock. The 4.9 kernel's existing charging inhibition is unchanged.

Trust and SELinux were checked concretely. Stock init and adbd are unchanged
static AArch64 ELF files (no PT_INTERP or PT_DYNAMIC); the helper is a **5,216-byte**
freestanding static ELF built locally from [source/diag.c](source/diag.c), with
no downloaded shell or shared-library closure. Its SHA-256 is
`ba8571e1c281d89eb9d43a870d4ef49ff4372055659c2c459c7cc62199985af8`.
The original policy is version 30, and recovery is **not** a permissive domain.
The legacy ASUS source libsepol could not parse its extended permission format;
a bounded **452,022-byte** AOSP Android 7.1.2 libsepol archive was used instead.
The archive is retained and hash-pinned for offline builds. Six additional AOSP
reference files total 116,567 bytes. Download origins/hashes are recorded in
[libsepol evidence](evidence/libsepol-download.json) and
[AOSP reference evidence](evidence/aosp-reference.json). References corroborate
behavior but are not a claim that vendor binaries were rebuilt from those tags.

[policy_patch.c](source/policy_patch.c) makes seven explicit grant additions:
init configfs file writes and link creation; shell/adbd read/search access to
tmpfs report files/directories; and adbd's fixed same-domain exec from its guard
to the stock binary. No permissive bits, types, block-device grants, or root
transition are added. [The exact delta](artifacts/candidates-v3/policy-delta.txt)
and [policy checks](evidence/verification-v3.json) show that report access and
the recovery reboot capability are permitted, while shell/adbd block writes
and tmpfs file writes remain denied. Actual type-transition queries confirm
that the report stays `tmpfs`, not an unreadable per-domain tmpfs type. This is
a targeted offline policy check, not exhaustive validation of every vendor
binary path or every possible AVC on hardware.

Only the public RSA material from `~/.android/adbkey.pub` was embedded; its
hostname/user comment was removed. The ADB private key was never read or copied.
Decoded public-key SHA-256:
`cb5409ebf18f82901424145b3be54dc3bba45f9ad17d493b984813c4fa0dc0fc`.
Possession of that key's private counterpart authorizes ADB to these images.
There is no framework authorization prompt or dynamic enrollment mechanism.
Authentication, unauthorized-host rejection, actual UID drop and transport
operation have **not** been runtime-tested. Images contain a linkable public
key, and reports may contain serials/cmdlines/kernel logs; keep them private.
Artifacts are ignored and candidate directories are mode 0700. Regenerating
with another public key intentionally changes image hashes.

Passed checks are recorded in [verification-v3.json](evidence/verification-v3.json),
[reproduction-v3.json](evidence/reproduction-v3.json) and
[tools-v3/build.json](artifacts/tools-v3/build.json):

- Both full recovery backups agree exactly, including the supplied SHA-256
  `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`
  and 16,740,352-byte size. Stock image decomposition/reassembly is exact.
- MTK KERNEL/RECOVERY wrappers, Android image IDs, addresses, partition limits,
  unchanged stock kernel, pinned 4.9 gzip/DTB, identical ramdisks and absent
  stale signature trailers pass. Ramdisk allowlist, service argv, filesystem
  mount types and write destinations pass.
- Helper compilation passes `-Wall -Wextra -Werror`; host ASan/UBSan tests use
  fake syscalls, never real reboot/device calls. They cover bounded/infinite
  input, read errors/EINTR, exact command rejection, UID gating, absolute
  deadlines, timer failures, normal reboot only, and refusal to launch adbd
  without enforcing SELinux or FunctionFS.
- Independent helper recompilation and two candidate-generation runs produce
  identical helper, images, compressed ramdisk and policy. Existing output
  directories are refused. Corrupted image ID, oversized image and unsafe
  archive paths are rejected.

No image was booted in an emulator or on the ASUS. These checks establish an
offline artifact, not successful init, USB, authentication, reset or hardware.

New-kernel reset evidence is pinned to the exact build commit
`717bb3c9e13ce573cfdd2dda856debd27a0fa17f`. Twelve local source files were hashed
against read-only VM source and match; see
[kernel-source-identity.json](evidence/kernel-source-identity.json) and
[source/kernel-reference](source/kernel-reference). Keypad probe calls the
long-press setup. `ONEKEY_REBOOT_NORMAL_MODE=y` and
`ONEKEY_REBOOT_OTHER_MODE=y`, with `KPD_PMIC_LPRST_TD=2`, select **14 seconds**
according to Kconfig, not five. PMIC wrappers ignore register-write errors;
this is an intended reset path, not verified physical behavior.
`machine_restart` calls the architecture restart hook or registered restart
handlers; mtk_wdt supplies the reset/notifier path. That hardware/firmware chain
has not run under this kernel. The watchdog probe stops the hardware timer
because DOUGLAS/GIZA are disabled; the diagnostic never opens/arms it. The
stock evidence is narrower: a user-confirmed five-second Power hold returned
from a fastboot transport stall, with one recorded success. Do not substitute
that observation for new-kernel reset validation.

A recovery-slot experiment is conditionally viable because normal stock
`boot`, `system`, encryption metadata and the root-capable stock userspace can
remain intact. The stock-kernel control must come first. Success would establish
acceptance of this modified image plus usable diagnostic init/ADB under stock;
it would not establish that 4.9 boots. Absence of ADB alone cannot distinguish
LK rejection from init/policy/USB failure. Record screen behavior, USB identity,
deadline return and report separately. A blank/unchanged boot logo is possible
because the helper draws no UI. Do not proceed to the 4.9 image merely because
the control image could be written.

The restoration procedure for a later, separately controlled experiment is:

1. Before any experiment, confirm normal stock boot and exact fingerprint,
   working authorized ADB, adequate battery, and successful on-demand root
   after a clean return through **Normal Boot**. Preserve both raw recovery
   copies and verify their complete hash above. Re-resolve the live by-name
   mapping and block size. Saved evidence places recovery at sector 160184,
   length 32696 sectors; use the partition node, never the firmware scatter
   offset or a whole-disk write. Root's independent reads already matched
   recovery, boot and LK, but no restore write was demonstrated.
2. Establish physical recovery-entry/Normal-Boot selection semantics without
   leaving an update/wipe request. Prefer a deliberately selected recovery
   boot over a persistent recovery command. Do not assume a normal reboot
   clears all LK/RTC/BCB recovery requests. Do not change `para`, seccfg, FRP,
   preloaders, LK or the normal boot partition as a workaround.
3. If the test fails, try the documented physical return and select Normal
   Boot. The software deadline helps only after it starts. If stock Android
   does not return, **this restore path is unavailable**: locked fastboot
   writes and BROM/DA restore are not proven. Stop further experiments rather
   than treating either as an established fallback.
4. Once normal stock Android and ADB return, re-establish root using the
   existing fingerprint/hash-guarded
   `../2026-11-05-asus-root-hardware-validation/scripts/root_shell.py`.
   Review the transaction before that invocation. Stage the **full original
   raw recovery backup** in stock scratch storage and verify byte count and
   content against the host copy. Restoration's only partition destination is
   `/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/recovery`.
   Restore all **16,740,352 bytes / 4087 blocks of 4096 bytes**, including the
   original signature and tail. Do not restore the shorter candidate or an
   extracted kernel. No executable partition writer is supplied in this spike.
5. Flush the completed restore, independently read back the entire recovery
   partition through the guarded root session, transfer that readback to the
   host, and require the exact original SHA-256. Stock Android 7 lacks the
   previously attempted `sha256sum`, so calculate/compare on the host. Also
   verify normal boot's full-partition hash remains
   `7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316`.
   Restore/check SELinux Enforcing, remove only the verified scratch copies,
   and check ordinary stock boot. The root wrapper has a 60-second child limit;
   stage, restore and readback as separately reviewed bounded transactions.

Remaining prerequisites: current-device preflight and root after a clean
Normal-Boot return; an evidenced recovery-failure return path or an explicitly
accepted remaining recovery risk by the parent/operator; review of the exact
recovery-only write/readback transaction; and preservation of data still not
covered by the existing partition backups. Full system/userdata backup is not
present in the reviewed record. Runtime checks for the control are image
acceptance, enforcing-mode ADB launch, authorized/unauthorized host behavior,
report retrieval, no eMMC mounts, and deadline return. The 4.9 probe additionally
needs actual reset/Power behavior, UDC enumeration and board/power validation.
These outcomes are not silently promoted to passed prerequisites.

To continue offline, use Python 3.12+ (tested 3.13), make, clang, and an
ELF-capable LLD. This build used Apple clang 21.0.0 and rust-lld/LLD 22.1.6
already installed locally. No VM or download is required. From this spike:

```sh
python3 source/build_tools.py --out artifacts/rebuild-v3 \
  --lld /OWNER_HOME/.rustup/toolchains/1.97.1-aarch64-apple-darwin/lib/rustlib/aarch64-apple-darwin/bin/rust-lld

python3 source/generate.py \
  --recovery ../2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin \
  --recovery-verify ../2026-11-05-asus-boot-access-audit/artifacts/device-backup/verify/recovery.bin \
  --kernel ../2026-11-05-asus-android17-kernel-backports/artifacts/linux-bpf-fd/bpf-fd-result/ASUS-P00A-BPF-FD-UNTESTED.Image.gz-dtb \
  --public-key /OWNER_HOME/.android/adbkey.pub \
  --tools artifacts/rebuild-v3 --out artifacts/regenerated-v3

python3 source/verify.py \
  --candidates artifacts/regenerated-v3 \
  --recovery ../2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin \
  --kernel ../2026-11-05-asus-android17-kernel-backports/artifacts/linux-bpf-fd/bpf-fd-result/ASUS-P00A-BPF-FD-UNTESTED.Image.gz-dtb \
  --tools artifacts/rebuild-v3 --evidence evidence/regenerated-v3.json
```

Use new output names on every run; do not run Python with `-O` because the
verification assertions are intentional. `capture_kernel_evidence.py` is an
optional read-only source-provenance utility and is not called by the offline
build/generator. Source changes should produce a new numbered candidate and
fresh verification evidence. Parent integration and any physical-test decision
remain outside this spike.
