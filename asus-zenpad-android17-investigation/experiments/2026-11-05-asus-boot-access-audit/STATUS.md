<!-- current-20261106 -->
Current checkpoint (6 November): ADB and on-demand root work; read-only backups and independent fastboot entry are verified. Image authorization and a demonstrated failed-boot restore remain unresolved. No flash or unlock has been performed. See the 6 November continuation below.

# Exact-unit boot access checkpoint

Verified 5 November 2026 local time (6 November UTC). The ASUS is back in stock Android 7, boot completed, verified boot green, SELinux enforcing, ADB UID 2000. Play services and Play Store remain installed. No root exploit, unlock, wipe, partition write or custom boot was performed.

## Cleared gates

The user confirmed that holding Power for five seconds returned the tablet from the earlier fastboot stall. An isolated libusb client now successfully communicates with this exact serial, `DEVICE_SERIAL_REDACTED`, through the observed fastboot USB ID `0bb4:0c01`, interface `ff/42/03`. Android uses a different USB ID, `0b05:601f`. The first query attempt used only the Android ID and sent nothing; the corrected query immediately returned fastboot version `0.5`.

Google's native macOS transport clears endpoint stalls on open. The alternate client does not. Successful libusb traffic establishes a working alternative; it does not by itself prove which native operation caused the earlier timeout. No global Android tools were replaced. The isolated venv uses pyusb 1.3.1, capstone 5.0.9 and the existing Homebrew libusb.

Live replies: product `ASUS8163_EW_380`, `secure=yes`, `unlocked=no`, boot/recovery each `0xff7000` bytes. The read-only `flashing get_unlock_ability` query returns `unlock_ability = 0`. These are saved actual replies, unlike the earlier failed runner's lost output.

The matching official LK registers read-only OEM partition listing/read commands with dispatcher flags permitting execution while secure and locked. Static analysis identified the raw 64 KiB streaming protocol. Runtime use confirmed that the listing agrees with the Android GPT evidence and that each selected partition-size getvar agrees before reading.

Sixteen areas have two independently received, exactly matching SHA-256 hashes: boot, recovery, lk, proinfo, nvram, protect1, protect2, asus_nvm, persist, seccfg, secro, para, tee1, tee2, and the two eMMC boot areas. Each pass totals 134,369,280 bytes. Both 4 MiB boot-area sizes are independently confirmed by Android sysfs (8192 sectors each). All streams ended with the expected OKAY.

The live boot image matches the complete official boot.img byte for byte, followed by zero padding. The live LK likewise matches the complete official lk.bin, followed by zeros. Both boot areas contain the complete matching official preloader at byte offset 2048. This corroborates the read protocol and the exact firmware used for static analysis. Different boot-area hashes are retained rather than normalized.

Raw backups are private local files under `artifacts/device-backup/{initial,verify}` with restrictive permissions and Git ignore rules. They were not uploaded to the build VM. `evidence/backup-manifest.json` contains only names, sizes and hashes. This is not a full-disk or user-data backup: raw GPT sectors, system, userdata and other partitions are not covered by this checkpoint.

Normal `reboot` through the guarded alternate client returned OKAY; ADB subsequently returned and `sys.boot_completed=1` was verified. See `evidence/return-to-android.log` and `evidence/after-probe-android-complete.txt`. The earlier immediate post-reboot check ran before Package Manager was ready; the later check verifies both Google packages.

## Remaining device gate

The exact live LK registers `boot` with `forbidden_when_lock_on=1`. Together with the actual locked-state reply, this rules out assuming that ordinary temporary `fastboot boot` is presently available. No boot command was sent. Its registration does not establish that every other route is impossible.

The ASUS-specific startup code references decrypting an ASUS key, compares a resulting string against device identity and branches to unlock handling. This is evidence of a vendor key flow, not proof that we can generate an accepted key. No standard `oem unlock` or `flashing unlock` registration was found in the traced registration function. The reported unlock ability is zero. We have not changed the OEM setting or invoked any unlock command.

The text-only, pinned mtkclient reference includes MT8163 support, but that is not proof of BROM/DA access or a compatible unlock method on this unit. Its generic V3 seccfg layout must not be applied blindly: this unit has the expected leading header/magic but zero version/size fields at the generic parser's offsets. That discrepancy needs analysis before using a generic unlock operation. No mtkclient payload or command has been executed. Root-exploit feasibility is still unproven.

A demonstrated restore route from a failed kernel boot is still absent. Fastboot backups and a successful reboot improve recoverability, but cannot establish locked-state flash authorization, signature acceptance or BROM access. Preserve both preloaders, LK and the exact live partition map. Never use the firmware ZIP scatter as this unit's raw flash map; many offsets differ.

## Continue

Keep the tablet in Android during source work. Audit the ASUS unlock/key and image authorization paths, and investigate a verifiable temporary-root/BROM route without changing bootloader security data. Establish a restore design and preserve user data before any operation that can wipe it. A custom boot or flash remains gated on that evidence and on the Android 17 kernel/userspace compatibility work.

Read-only query script: `scripts/fastboot_readonly_usb.py`. Backup receiver: `scripts/backup_partition_usb.py`; default is plan only, and `--execute` is required. The fixed boot-area commands are based on the matching LK handlers, not invented GPT aliases. Return command: `scripts/return_to_android_usb.py`. Do not invoke an OEM raw-read command through an ordinary fastboot client, which expects standard status framing rather than raw partition bytes.

A metadata-only temporary-root check found `/proc/mtk_cmdq` (root-owned, readable to ADB shell). A zero-byte `dd` open succeeded without an ioctl or reading memory. The firmware security patch is 2018-06-01. These make the historical CMDQ/CVE-2020-0069 route worth auditing, but do not demonstrate a vulnerability or root. References: [Quarkslab original reverse-engineering](https://blog.quarkslab.com/cve-2020-0069-autopsy-of-the-most-stable-mediatek-rootkit.html) and [Google CTS regression source](https://android.googlesource.com/platform/cts/+/14b651dce31a04f54e59604e710494cc2df2daa6/hostsidetests/securitybulletin/securityPatch/CVE-2020-0069/poc.c). Neither exploit nor regression PoC was run. The original author’s XDA thread fetch timed out; do not substitute an unverified binary mirror.

Later checkpoint: the user explicitly authorized root, and the sibling `2026-11-05-asus-root-hardware-validation/STATUS.md` records successful on-demand root, independent Linux-block reads matching boot/recovery/LK, and private raw primary/backup GPT copies with valid CRCs and all 26 partition entries matching. Root feasibility and raw-GPT access are now cleared. The locked bootloader, failed-boot restore route and remaining full-system/userdata backup gaps are still unresolved. The tablet is back at Nova with SELinux Enforcing.

Flash-readiness continuation: no full Android 17 ROM image exists; only init/ADB/header modules and the unbooted diagnostic kernel. The user explicitly authorizes flashing once confidence is sufficient. A new `2026-11-05-asus-brom-recovery-proof` spike tests independent recovery access while the user is physically present. Pinned primary-author Z380M Alpine logs demonstrate BROM/legacy DA access on another unit, with the first 25 partition layouts matching ours and a larger userdata partition. They do not record that unit’s LK lock state or firmware provenance, so they do not prove that our locked unit accepts a custom boot image. The historical Z380M locked-bootloader TWRP thread is a lead, but original-page retrieval currently fails; no recovery image has been downloaded or trusted from it.
# 6 November continuation: authorization and stock recovery

The goal is active again. The user restored the tablet's USB connection and GCP
authentication. Authorized ADB again confirms fully booted stock WW 5.3.20,
verified boot green and SELinux Enforcing. No new reboot, flash, erase, unlock,
security-driver ioctl or raw register write was performed in this continuation.

The exact live-matching LK reads a fixed 0x1860-byte security record and decrypts
0x1830 bytes starting at 0x2c, despite this device's zero version/size/crypt-length
header fields. Its decrypted lock attribute is at 0x854. The saved record has the
expected end marker at 0x185c. The pinned mtkclient software cipher fails the
status/attribute validation checks on this record. Do not synthesize a generic
seccfg unlock image from these header values. Reproduction and bounded annotated
disassembly are in scripts/audit_saved_security_config.py,
scripts/disassemble_lk_authorization.py and evidence/saved-security-config-audit.json.

Root read-only boot-log collection found the stock /dev/sec node but no retained
security-policy lines. The published ASUS kernel Makefile selects asfv2, whose
handler lacks SEC_SECCFG_DECRYPT; the older unused asf handler includes it and
also changes in-memory lock tracking. No unsupported ioctl was probed. The
published source is 3.18.22 versus the running 3.18.35 release, so source evidence
is not a proof of exact runtime driver equivalence.

Both matching stock recovery backups were parsed without executing or extracting
their archive entries. The MTK RECOVERY wrapper is valid; 158 cpio entries were
inventoried. Production recovery has ro.adb.secure=1, ro.debuggable=0 and adbd
disabled; its device init configures MTP. Entering it alone would not establish
an unattended ADB restore route. No recovery reboot or update was performed.
See evidence/stock-recovery-ramdisk-audit.json and scripts/inspect_stock_recovery.py.

Four additional areas (metadata, kb, dkb, frp) now have independent matching root
reads in the sibling root-validation spike. Full system/userdata backups and a
demonstrated failed-boot restore remain outstanding. Android 17 networking module
builds and an isolated BPF configuration/kernel candidate have progressed; see
the sibling device-product, backport and virtual-validation checkpoints. This
does not establish custom-image authorization or flash readiness.

