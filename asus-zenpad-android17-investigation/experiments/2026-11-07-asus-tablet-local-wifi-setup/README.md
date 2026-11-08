# Enable ASUS Wi-Fi ADB from a local terminal

Question: can the stock ASUS enable authenticated Wi-Fi ADB without working USB data?

Status: prepared for an on-tablet Termux attempt; not yet executed on hardware.
Uses the exact existing on-demand root binary already verified on this ASUS.
App-terminal execution is supported by the upstream approach but is unproven on
this tablet. No ROM, partition, bootloader, or permanent root installation.

Outputs: `public/setup.sh`, `public/root-actions.sh`, and hash-pinned
`public/mtk-su64`. Serve only this public directory on the Mac's private LAN.

Continuation: install Termux's Android-7-compatible build from F-Droid; with the
tablet and Mac on the same Wi-Fi, download and run setup.sh. It checks exact
stock identity and binary SHA, sets the ADB TCP port to 5555, restarts only adbd,
and restores Enforcing. Keep the terminal open until it completes. Then connect
the existing Mac ADB client to the tablet and accept its RSA prompt. Verify the
serial, secure ADB and Enforcing before proceeding with the recovery installer.

The experiment's recovery probe currently reports over USB only. Local Wi-Fi
access does not establish a usable full-OS rescue path. A microSD-backed report
or rescue implementation remains a separate potential route.

## Recovery transport finding

The existing BMC kernel resolved.config already enables MMC_MTK, MMC_BLOCK,
MSDOS partition parsing, FAT/VFAT and ext4; no kernel configuration change is
indicated merely to try an SD card. Physical SD operation remains unproved.
The current rescue proxy is an authenticated UID2000/domain-bound Unix-socket
client reached through ADB. It has no local-card installer. Its mounts_clear()
also rejects every major179 mounted device, including an SD card: any future
card adaptation must preserve rejection of mounted internal eMMC while allowing
a verified separate read-only SD source, rather than removing the mount check.
Do not call the existing USB-only rescue SD-ready. Await card availability
before implementing a separate route.

USB bootstrap session32176 terminated with a 300s timeout, attempt
9988bab5-eb78-4e1a-8d85-610088f4f7c0, with no mutations. Do not restart it: user
has now confirmed the USB data hardware failure.

## Correct macOS USB inventory API

This Mac exposes SPUSBHostDataType (confirmed via system_profiler -listDataTypes), not SPUSBDataType. The old SPUSBDataType and IOUSB-plane queries returned empty and must NOT be used as evidence of no USB devices. Fresh SPUSBHostDataType inventory sees USB hubs/dock, RTL9210B-CG storage, keyboard/mouse devices; still no ASUS or recognizable card reader. Diskutil physical inventory remains the independent evidence that no SD block device is currently present. No device, disk, driver or USB change was made. Wi-Fi access remains the next useful route.
