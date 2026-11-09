# Physical checkpoint — 2026-11-08

Latest: property-gate paired trial passed; recovery RAM capsule deployed/read-back verified, boot not yet attempted at this write. See evidence/recovery-deployment-receipt.json. Stale BCB wipe arguments reconciled. Normal BOOT remains original. Earlier preservation/no-deployment statements below describe the pre-deployment checkpoint.

Alpine3.24.4 aarch64 runs on this tablet's original Linux3.18.35 in a temporary RAM chroot. This is actual tablet execution, not emulation. Donor HEAD remains7218a276f252a59874ab860683c061fa2b856519; official stable release and minirootfs checksum were rechecked. Android17, Linux4.9 and cloud infrastructure remain parked.

## What passed

- **Native Alpine Wi-Fi station:** stopped Android station management, retained the original stock WMT launcher, powered WLAN through the stock node, associated with Alpine wpa_supplicant2.11/nl80211, obtained a BusyBox DHCP lease and fetched HTTPS. No original network profile was edited. This qualifies native station tools, not WMT initialization from a cold kernel.
- **Alpine applications:** current apk, BusyBox, curl, Python3, OpenSSL3.5.9 and SQLite3.53.4 executed on3.18.35. Package installation over Wi-Fi worked.
- **SSH workload:** during a verified, temporary Permissive root window, a Mac SSH client connected through USB forwarding, executed an Alpine shell, committed/read SQLite and fetched HTTPS. Key-only login. Listener expired and forwarding was removed. Under Android Enforcing, sshd re-exec is denied; permanent LAN SSH is not qualified.
- **Desktop:** Xorg21.1.25, JWM2.4.6 and the adapted donor bridge ran through a20second trial. Live Goodix ioctls report X0..800, Y0..1280, slots0..15. The patch rejects missing ranges instead of using ELAN values. Xinput attached touch0. No physical taps were observed, so corner mapping/click/drag remain unverified.
- **Browser/dashboard:** NetSurf3.11 rendered a live local Python HTTP+SQLite dashboard. Actual requests and database writes passed. [Captured X display](../artifacts/asus-alpine-dashboard.png),800×1280, was visually inspected. This qualifies a simple dashboard, not arbitrary modern JavaScript applications. The image loader reports running without its sandbox; no bypass was added by this project.
- **microSD persistence:** only a new dated Alpine folder was created. SQLite data was copied to it and that directory bound into the RAM root. Verified VFAT backing device; writer committed, sync completed, a separate process read the marker. Not a reboot or power-loss test.

## Restoration and preservation

Android display services returned running after timed GUI trials. Stock Wi-Fi COMPLETED, IPv4 lease and HTTPS were verified after waking the display. SELinux Enforcing was restored after root sessions and after an isolated diagnostic cleanup.

Screen-off PNO scans fail on the stock driver, leaving Android disconnected after a Wi-Fi handover. Opus5.5 identified the exact framework log sequence; waking the screen restored normal network selection. Future handovers must check a real connection, rather than only the daemon's state.

Fresh full partition hashes show **both BOOT and RECOVERY currently match canonical stock backups**:7bb68511... and902b2f06..., respectively. This supersedes the handoff's stale diagnostic-recovery statement. No internal partition writes occurred in this spike. BCB first2048bytes were privately captured: command empty, recovery field is still `recovery\n--wipe_data`. Do not enter stock recovery until that stale request is reconciled. GPT, bootloader, original factory/calibration and rollback archives remain untouched.

Existing SD rescue folders were neither modified nor executed. New folder: `2026-11-08-asus-alpine`, containing marker, software archive preparation, service database and private local sidecars. Sidecars preserve original WIFI/WIFI_CUSTOM and a single connected station profile; only a public SSH key is staged, never its private key. Private source captures and raw logs stay under ignored private/ outside the donor repository.

## Remaining cold-start gate

Stock Wi-Fi dependencies include original wmt_loader, resident wmt_launcher, firmware path aliases, WMT character nodes, private calibration, supplicant and DHCP. Bionic ELF closure uses linker64 and stock libraries; fresh process maps and private hashes are saved.

An isolated launcher probe exposed missing /dev/urandom, then /proc/self/exe. With those present, it repeatedly queries absent Android logging endpoints and sleeps before any stpwmt open. It imports property_get/set and contains service.wcn.driver.ready and chip-ID property names. The exact branch/readiness contract must be determined before enabling automatic WMT startup outside Android. A normal TERM timeout did not stop this diagnostic; exact executable/PID checked SIGKILL stopped only the isolated process. Original resident WMT was untouched and Enforcing restoration was verified. Use a kill-after deadline for future probes. Do not call `-h` a harmless help operation for this binary.

[Offline recovery capsule](recovery-capsule.md) is built from the byte-identical original stock kernel. No deployment. It uses a bounded RAM root, stock SYSTEM read-only, SD read-only, USB serial shell, no GUI and no BCB/raw-write behavior. Automatic cold Wi-Fi is gated off until readiness is understood. Locked LK prevents assuming fastboot RAM boot; this capsule would require a carefully reviewed, reversible recovery-slot write, with BOOT/SYSTEM/DATA retained.

## Artifacts and continuation

Read this checkpoint, MEMORY.md and reports/recovery-capsule.md. Detailed private evidence is in private/live/. The software root archive was captured over ready-signalled USB SSH and compressed on the Mac. Its4978 archive members passed marker/path/private-exclusion checks; compressed size155,528,718 bytes, SHA256 b66439ef6641e7e1b0649c78c6308d1a3daa1393dd25f1fe47bfba0f8100934e. See private/live/sd-rootfs-stage.txt for card-copy checksum verification. Tablet-side gzip had exceeded its48second bound and left an incomplete `.partial`; the staging script removes only that owned partial after successful final-copy verification. No capsule deployment. Opus5.5 is analyzing the precise property-readiness branch before the next hardware experiment.

The512MiB RAM tree remains `/data/local/tmp/asus-alpine-ram`; reboot discards it. Installed footprint after OpenRC:372.1MiB/184 packages. Android mount remount syntax stacked an empty tmpfs; only that mount was removed, original data retained, and direct MS_REMOUNT verified exact capacity and stable device number. Use explicit Alpine PATH for chroot subprocesses. Historical trial scripts are not a run-all installer.
