# Independent recovery access checkpoint

6 November 2026 UTC (5 November local). The user explicitly authorizes flashing once confidence is sufficient; no further permission is needed within that scope. Readiness is not established, and no flash, erase, unlock, watchdog initialization, download agent or RAM payload was sent in this experiment.

## Current device state

USB returned on a different physical port (1-1.1.1), and authorized ADB confirmed fully booted stock Android, verified boot green and SELinux Enforcing. A normal reboot with the native reader armed did not expose a captured download session. A later controlled shutdown exposed the preloader serial port again. The final preloader-to-fastboot mode test succeeded, and a fastboot reboot returned to fully booted stock Android. Play services and Play Store are still installed. The current physical USB connection gate is cleared; see the verified roundtrip evidence below.

## Attempts and evidence

The initial snapshot confirmed stock WW 5.3.20, boot_completed=1, verified boot green, SELinux Enforcing, USB charging at 99% and 29°C. No Android 17 binary was installed.

The bounded serial receiver uses pinned mtkclient handshake/metadata protocol. Its first BROM-only wait observed the preloader PID 2000 but no PID 0003. A second receiver allowed both IDs. It opened /dev/cu.usbmodem111200 at physical location 1-1.1.2, received READY startup bytes, and stopped before any metadata query because the expected handshake echo did not appear. Handling one READY notification still left repeated READY bytes. All those attempts sent only handshake bytes; none reached FD/D8/FC chip queries. The tablet returned to Android after those attempts before later user/menu interaction.

The repeated failures triggered a premise audit, recorded in evidence/handshake-premise.json: the observed interface may not accept the download handshake under our chosen serial configuration. The custom serial reader used 115200/default DTR, while upstream native USB sets 921600, RTS set and DTR unset. That difference remains a hypothesis until a matched native observation is made; repeated READY alone does not prove a particular security or META state.

Upstream mtkclient is cloned at 118a000a83ea31c4f427fe5225abfe964546e05e in its own preserved Git repository. A source-reviewed gettargetconfig --skipwdt command was selected to avoid watchdog/register writes, payloads, DA uploads and storage mutations. Its first run failed before device access: upstream converted USB IDs to a nested dictionary but Mtk.setup still expected a list. The minimal saved patch fixes explicit VID/PID filtering to the actual dictionary representation. A real constructor check verifies the exact 0e8d:2000 filter and disconnected state. The patched native read attempt then timed out after 70 seconds without detecting that device; it therefore did not test the download protocol or establish an authentication result. Logs and the exact patch/hash are retained. Missing FUSE is only an unused-filesystem-feature warning; the metadata command starts normally after the dictionary adaptation.

scripts/run_upstream_config.py runs only that fixed metadata command with skipwdt and a bounded process deadline. Do not substitute printgpt or another command without reviewing its RAM/DA actions. scripts/read_chip_info.py is the earlier bounded serial receiver, retained as failed diagnostic evidence rather than an established working transport.

## Primary-source lead

The kaantcp/z380m-alpine project at 7218a276f252a59874ab860683c061fa2b856519 publishes real Z380M BROM/legacy-DA/readback/boot logs. Source and evidence are pinned in the sibling boot-access-audit spike. Its first 25 partition offsets/sizes match this unit; userdata has the same start but is larger. Its guide's exact-size checker must not be used as authority for our different userdata capacity. Use this unit's CRC-verified GPT exclusively.

The reference log reports MT8163, SBC enabled, SLA/DAA disabled, and a successful BROM payload/legacy DA session. Those are another unit's observations. Its prior LK lock state and original boot-image provenance are not established, so its custom boot does not prove that ours will boot while locked. The historical Z380M locked-bootloader TWRP thread is another lead, but its original page could not be retrieved (502); no recovery binary was downloaded or trusted from it.

## Flash readiness

All sixteen existing critical-area backups were rehashed successfully this turn. The independent Linux-block cross-checks and both raw GPT CRC validations from the root spike remain available. Full system/userdata backups and a demonstrated failed-boot restore route are still absent.

The Android 17 checkpoint contains compiled init, device ADB APEX and kernel headers, not a complete ROM. Full image generation is disabled. The experimental 4.9 kernel has never booted and intentionally inhibits charging; modern kernel features, HAL/policy integration and hardware validation remain incomplete. No candidate currently satisfies Android 17 flash readiness. A recovery-only test may become appropriate after independent recovery access, exact image provenance/packaging, rollback and physical mode handling are demonstrated.

## Continue

First recover a known connected state from the current boot menu/physical situation. Once Android/USB returns, arm the patched native read-only metadata reader and use one normal restart to observe the preloader with the upstream USB control setup. Establish actual chip/security metadata, then separately review any RAM-only DA/GPT read test. Preserve normal boot, system, LK, both preloaders and all user/Google data. Do not infer restore ability from handshake alone.

GCP remains stopped; this work created only local isolated tools, source/evidence files and a small virtual environment. No cloud resource was provisioned.

## Verified preloader mode route

A controlled comparison configured the serial port to match upstream native CDC settings (921600, DTR false, RTS true) and transmitted only one A0 handshake byte. The observed response was repeated READY, without the expected 5f. This is evidence against treating that preloader interface as a standard BROM/download session under either tested serial setup. The pinned upstream META implementation explicitly handles READY as a mode-selection greeting. The exact official preloader, previously matched to both boot-area backups, contains READY, FASTBOOT, TOOBTSAF and DISCONNECT constants as well.

The fixed mode-request receiver was armed on the exact observed USB location. The user started the tablet using Power with USB connected. It received READY, sent only FASTBOOT, and the serial interface disappeared immediately afterward. The textual TOOBTSAF acknowledgement was not captured and DISCONNECT was not sent. The original script reported the serial disconnect as an error; this does not establish failure of the mode switch. Independent fastboot enumeration matched DEVICE_SERIAL_REDACTED, and the guarded alternate USB client received actual version 0.5, secure=yes, unlocked=no and unlock_ability=0 replies. A normal reboot then returned OKAY and stock Android/Google packages were verified. This establishes an observed preloader-to-fastboot entry route without Android. The receiver now handles this firmware's immediate USB handoff only by independently verifying the exact fastboot serial/interface; it never treats an unconfirmed disconnect as success. No extra reboot was performed merely to test this reporting adaptation.

This is not BROM/DA access, an unlock, or a proven storage restore path. The custom boot handler remains forbidden while locked and no full Android 17 ROM exists yet. The preloader mode route is useful progress, not flash readiness.

The exact official updater script was also checked: restoring the full OTA writes both eMMC preloader areas before system and boot. It must not be described as a boot-only rollback or used as a casual recovery test. No OTA was applied.

Next: retain the now-proven independent fastboot entry path, resolve image authorization/restore access, and finish the Android 17 kernel/system/HAL integration. A stock-recovery entry test may provide further evidence without altering an image, but any full-OTA write needs its own concrete restore design and preservation of user data. GCP remains stopped. Current verified state: Android boot_completed=1, original fingerprint, verified-boot green, Enforcing.
