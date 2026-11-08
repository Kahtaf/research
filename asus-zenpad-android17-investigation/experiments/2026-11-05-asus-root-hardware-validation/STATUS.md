<!-- current-20261106 -->
Current checkpoint (6 November): on-demand root is verified and SELinux is Enforcing. Four more key/metadata areas have matching duplicate backups, held only in the ignored local private directory. Full userdata backup and experimental-kernel hardware validation remain outstanding. See the additional preservation checkpoint below.

# Root and hardware checkpoint

5 November 2026 local / 6 November UTC. Temporary root is demonstrated repeatedly on this exact stock WW 5.3.20 unit. No boot image, system partition, bootloader security state or preloader was changed. SELinux was restored to Enforcing after each completed root session. Stock Android remains booted, Nova is home, and Play services/Play Store remain installed.

## Root method and limits

The historical MediaTek CMDQ interface `/proc/mtk_cmdq` is present and can be opened by ADB shell. After metadata-only checks, the user explicitly authorized root. A bounded mtk-su run successfully obtained UID/GID 0 and full reported capabilities. The child shell read a root-protected file and then restored SELinux Enforcing. `temporary-root-proof.json` records the actual identity/protected-read proof. Subsequent root sessions successfully read raw block devices and input/power diagnostics.

`scripts/root_shell.py` provides repeatable **on-demand ADB root** for this exact model, SDK and fingerprint. It verifies the binary hash and restores Enforcing when its child shell exits. Feed a reviewed script on stdin. For example:

```sh
printf 'id\n' | python3 scripts/root_shell.py
```

No Magisk/SuperSU daemon, application superuser manager or automatic root at reboot is installed. An ordinary ADB shell remains UID 2000. This method can be invoked again after reboot while this vulnerable stock firmware remains installed; it has not yet been retested across another reboot. Do not describe this as a persistent boot-image root or an unlocked bootloader.

Binary provenance: the original author's thread/attachment host reset connections or returned HTTP 403. The executed 64-bit copy is the preserved mtk-easy-su asset, pinned repository revision `59d4037547899869df48e37b315d778a1226ec6c`, SHA-256 `328632e853ff6427af9f35cb83a91d9e960f35d01188ee66d46ae9c7ce7c7827`, 65,144 bytes. Its LFS pointer verifies that hash, and file history traces it to the integrator's 22 December 2020 release commit `7dfdd89db038e85dd210f0aa66769935a77a9554`. This is a documented third-party preservation, not an author signature verification. The other inspected mirror is ARM32 and has a different hash; no claim of identical copies is made. ELF architecture, interpreter, imports and embedded attribution were inspected. The full app/its other bundled binaries were not installed, and Play Protect was not disabled.

Two harness issues were corrected: mtk-su's `-c` accepts one executable rather than a shell command list, so `/system/bin/sh` is now invoked with commands on stdin; stdin must be read before ADB preparatory calls consume it. The initial failed command run did obtain root and set Permissive; the immediate corrected run restored Enforcing. Both attempt/proof logs are retained. One baseline script reached GPT backup but then encountered Android 7's missing sha256sum command. The host computed and validated the pulled-file hashes instead; that script has been corrected for continuation.

## Hardware evidence on stock Android

| Component | Observed | Remaining test |
| --- | --- | --- |
| Wi-Fi | Connected; 3/3 internet pings, 0% loss; DNS lookup and domain ping succeeded | Longer transfer, reconnect, suspend/resume |
| Bluetooth | Controller STATE_ON; Settings discovery displayed ten nearby devices | Pairing, audio/data transfer with a known peer; optional user question pending |
| Charging | USB online; main battery Charging/Good, 99%, about 4.25–4.26 V and 30.0°C; charger input about 4.84 V in the captured sample | Actual charge gain at lower state of charge, unplug/replug, sustained thermal behavior |
| Touchscreen | Real Goodix event11, direct input, 800×1280 bounds and 16 touch slots registered | Physical full-screen/multitouch test; optional user question pending |
| Display/UI | Screen powered on; Settings, Bluetooth page and Nova rendered; automated UI navigation worked after waking with Power | Physical brightness/uniformity and suspend/resume |
| Sensors | Accelerometer service active; sensor input devices present | Physical orientation/motion checks |
| Audio/camera | Packages retained | Speaker/microphone, camera preview/capture and Bluetooth audio not established |

A 20-second read of the actual Goodix event node observed no physical touch events. The user had not confirmed performing the requested touches, so this is inconclusive, not a touchscreen failure. Injected automation events cannot prove a working physical digitizer. The legacy timeout returned 143; the receiver handles that and 124 on future runs. The root wrapper restored Enforcing after the sample. The tablet was returned to Nova and the temporary USB stay-awake setting restored to its original value 0.

The absent optional cover reports impossible battery values (for example -273.1°C and capacity -1). Its PRESENT=0; those are not the main battery readings. The fuel-gauge debug current counter was read, but its sign/calibration was not established, so it is not a claimed charge-current measurement.

These are stock-firmware tests. The experimental 4.9 kernel has never booted, and its diagnostic DT deliberately inhibits charging. Do not infer that these hardware functions work under the port or enable charging there without further validation.

## Stronger backups and map

The sibling boot-access spike holds two matching reads of sixteen device areas (134,369,280 bytes per pass), including both 4 MiB eMMC boot areas and factory/calibration partitions. Root then independently read boot, recovery and LK through their actual Linux block devices. All three hashes exactly match the OEM fastboot reads. See `evidence/direct-block-read-verification.json`.

Both raw GPT tables were backed up with root, retained privately under `artifacts/private`, and parsed on the Mac. Both header CRCs and partition-array CRCs pass. Their entries agree with each other, and all 26 entries match the previously collected live map. `evidence/raw-gpt-verification.json` records the checks. Only scratch backup copies were removed from the tablet after successful host verification. This still does not include full system/userdata or prove a restore route from a failed boot.

Stock kexec discovery found no kexec sysfs interface or machine_kexec/kernel_kexec implementation names. The syscall names are weak symbols; addresses remain masked even in the root shell, so exact alias equality was not established. Do not assume root provides a functioning RAM-only kernel-boot route. No kexec syscall was invoked.

## Further debloat

The existing reversible debloat workflow disabled AppCloud promotions (`com.ironsource.appcloud.oobe.asus`) and ASUS Game Broadcaster (`com.asus.gamewidget`) after inspecting their components. Total disabled optional candidates: 17. All Google package states were unchanged during this pass, all previously disabled packages stayed disabled, and all retained packages/defaults passed. No APK or app data was deleted. The exact undo journal is in `../2026-11-04-asus-zenpad-debloat/runs/20261106T025111.159949Z`.

## Continue

Use on-demand root for diagnostics and remaining backup gaps. Preserve all Google components and hardware/power services. Finish physical touch and Bluetooth/audio tests when the user can supply those observations. The Android 17 port still needs a validated unlock/unsigned-boot and restore route, modern kernel feature work, legacy HAL integration and hardware tests under the new kernel. Root success does not clear the locked bootloader gate.

Final checks: the fingerprint-guarded root helper again returned UID/GID 0, then the normal ADB check confirmed Enforcing and boot_completed=1. Google states still exactly match the latest debloat baseline and all retained packages/defaults pass. Play Store was foregrounded and its Games/Apps tabs rendered; no authenticated download was attempted. Nova was restored afterward.
# 6 November: additional preservation and security-log reads

Authorized ADB returned after the user reconnected USB. On-demand root was
verified again; boot-security log collection was read-only and found /dev/sec but
no retained SEC_POLICY/seccfg boot lines. The logs are private under artifacts.
SELinux returned to Enforcing, stock Android completed boot, verified boot was
green, and Play services/Play Store paths remain present. No package or persistent
system/security setting was changed.

scripts/backup_encryption_areas.py made two independent reads of metadata, kb,
dkb and frp, 38797312 bytes per pass. All four second reads match their first
copies. Exact sizes are checked against the saved live GPT and block sysfs before
copying. Private local backups are under
artifacts/private/encryption-area-backup-20261106T052822Z; no raw contents were uploaded.
The manifest/evidence is evidence/encryption-area-backup-20261106.json.

Only fixed temporary copies under /data/local/tmp were written, then removed.
No raw block, encryption metadata, key area or FRP write was performed. Final
SELinux is Enforcing. These four snapshots add preservation evidence; they are
not a full userdata backup, an encryption-key usability test or proof that a
complete restore will succeed.

