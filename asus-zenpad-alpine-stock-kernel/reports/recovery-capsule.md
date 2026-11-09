# Stock-kernel RAM recovery capsule — offline only

Status: the current optional-persistence revision is built and format-checked, **not deployed or booted** by this implementation task. The parent has separately demonstrated independent Alpine PID1, cold stock WMT/WLAN and pinned LAN SSH after correcting mdev device permissions at runtime. This revision retains those source corrections and adds optional service-state persistence; its automatic mount/key/service behavior still needs physical qualification. No installer is provided.

The image uses the canonical stock recovery header and MTK `RECOVERY` ramdisk wrapper, plus the **byte-identical kernel from this tablet's original BOOT backup**. Original BOOT and recovery kernels match each other. Only the recovery header's ramdisk size and image ID change; no kernel, command-line, load-address or bootloader changes. The full padded image is 16,740,352 bytes; approximately 8.4 MB is used. The bootstrap ramdisk is approximately 936 KB compressed and contains Alpine3.24.4 BusyBox and its exact musl interpreter, both from the checksum-verified minirootfs already run on this kernel.

Outputs are ignored under `artifacts/recovery-capsule/`: `recovery-alpine-stock-ram.img`, compressed ramdisk and `manifest.json` with exact image/kernel/bootstrap hashes. Build deterministically with `python3 scripts/recovery-build.py`; it reads only canonical stock inputs and local source files and never opens a device.

Current optional-persistence image SHA256: `f3e574cf499fc903883ba7f5850aa02fdb87642a56af9d32627b39ccf44a2748`; full bytes `16740352`, used bytes `8417280`. The kernel remains byte-identical to both canonical originals. Parent preflight confirmed raw ioctl formatting and the actual WMT class paths/SYSTEM geometry.

## Runtime contract

- Legacy `android_usb` ACM, using donor-proven MediaTek VID/PID and a generic nonprivate serial string. The bootstrapped USB root shell is physical-cable access without a password, as in the donor approach. Mac USB-serial observation has not been tested with this image.
- No-devtmpfs startup creates initial character nodes and runs mdev. Later WMT nodes use the running kernel's sysfs major/minor numbers.
- Only actual SD `mmcblk1p1` is considered, with parent device type required to be `SD`. It initially mounts read-only with nosuid/nodev/noexec, root uid/gid, fmask0177 and dmask0077. It never scans or executes old `asus-stock`, `asus-rescue` or Android17 triggers.
- `/2026-11-08-asus-alpine/ALPINE.ID` must start with `asus-alpine-stock-kernel-v1`.
- Root archive is `alpine-3.24.4-ram-rootfs.tar.gz` in that same directory. Its sidecar must be named **`alpine-3.24.4-ram-rootfs.tar.gz.sha256`** and begin with the lowercase64-character SHA256 digest. Hash and the extracted `/etc/asus-alpine-ram-release` marker are checked before handover.
- Root is a bounded768MiB tmpfs. SYSTEM must match mmcblk0p25 start1072424/sectors7331840 and mounts **`ro,noload`**, preventing journal replay writes. Parent must independently confirm fresh live geometry before deployment; these expected values match retained original GPT evidence.
- `/vendor` resolves to `/system/vendor`; `/etc/firmware` is a RAM view of stock SYSTEM and vendor firmware files. No firmware is published or altered. This does not prove every path compiled into this exact kernel; notably the source-only `/system/etc/firmware/WMT_SOC.cfg` lead remains a cold-start qualification question.
- Existing private `WIFI`, `WIFI_CUSTOM`, `wpa_supplicant.conf` are copied from the new SD directory's `private/` into RAM. Missing calibration/profile fails into rescue instead of regenerating defaults. Optional `authorized_keys` is public-key material only. Host private keys are generated in RAM by default; the optional state gate restores/preserves them from the marked private SD directory.
- A controlled BusyBox inittab replaces only the extracted RAM root's inittab. The capsule starts a USB shell and key-only SSH port2222. **No GUI starts automatically.** OpenRC remains installed in the root archive but its generic boot mount scripts are intentionally not used for the first capsule experiment.
- SYSTEM stays read-only. SD stays read-only unless the exact optional persistence marker is present. Then only the new dated folder supplies mutable service data and stable SSH host keys; root software and logs stay in RAM. This implementation does not yet establish physical persistence across reboot.
- There is no raw partition write, BCB reader/writer, stock recovery invocation, wipe handler or automatic reboot in these scripts. Pre-handoff failure stays in a rescue shell. This does not reconcile a preexisting BCB `--wipe_data`; the parent must resolve that before any recovery entry.

## Optional service-state persistence

See [recovery-state.md](recovery-state.md) for the exact marker, protected mount contract, host-key lifecycle and parent acceptance steps. The integration is prepared offline, not a claim of reboot persistence.

## Cold Wi-Fi readiness

The exact stock launcher property gate is now physically proved in a hardware-free sealed subtree: `ready=no` never opened stpwmt; `ready=yes` reached14 stpwmt opens returning ENOENT, with WMT nodes absent throughout. See `reports/opus-wmt-readiness.md` for exact-binary analysis and the parent's private `experiment-10-property-gate.txt` for physical controls. This proves the single-file stock property-area format and readiness branch, **not cold module initialization**.

Automatic cold Wi-Fi is still off unless the parent intentionally creates `COLD-WIFI.ENABLE` containing `asus-alpine-stock-wmt-v1` in the new SD directory. With it present, this revised capsule:

1. Requires no inherited property area and creates a once-per-RAM-boot loader-attempt marker before running the stock loader.
2. Runs that loader once under `strace --kill-on-exit -f -X raw -e trace=ioctl`, with a TERM deadline followed by KILL. Loader exit status and ioctl trace stay private in `/run/asus-alpine/`, mode0600.
3. Ignores process exit status as readiness: the loader returns a failed property_set status even after successful module initialization, and its own ready setter can also follow a failed init.
4. Requires **exactly one ioctl request0x80047704 returning0**, plus exactly one live stpwmt sysfs class. It creates device nodes from the actual class device numbers and requires character nodes.
5. Only then generates root:root0444 `/dev/__properties__` with the sole property `service.wcn.driver.ready=yes`, before launching the stock resident binary. There is no property daemon, preload shim or chip-ID override; the chip-ID property remains absent, preserving the original kernel-ioctl fallback.
6. Starts native nl80211 supplicant/DHCP and key-only SSH. No GUI is enabled.

The property generator is copied into the capsule from the parent's physically validated `scripts/wmt-property-area.py`; its source hash is in the artifact manifest. `scripts/recovery-validate-wmt-loader.py` rejects missing, failed, duplicate and incomplete module-init evidence. The parent has subsequently proved that cold sequence and LAN access, after fixing public device-node permissions overridden by mdev. The revised capsule retains chmod666 after mdev and enables loopback before services; a later untouched boot must confirm these integrated fixes.

Minimum SD enable inputs, all under `/2026-11-08-asus-alpine/`: `ALPINE.ID`, the software archive and its exact-name `.sha256` sidecar, `private/WIFI`, `private/WIFI_CUSTOM`, `private/wpa_supplicant.conf`, optional `private/authorized_keys`, and **`COLD-WIFI.ENABLE` only for the reviewed cold-init experiment**. The software archive itself needs `/etc/asus-alpine-ram-release` and installed Python, strace, native supplicant/DHCP and SSH tools. No secret belongs in the image or software archive.

Before switch_root, rescue tracks the device, log and proc locations after every mount move. A failure after moving `/dev` or `/run` therefore still opens the actual USB serial node and RAM log. The exec/switch_root handoff remains the normal PID1 point of no return and needs physical qualification.

## Validation performed

- Both canonical input image SHA256 hashes match their recorded originals.
- Wrapped stock kernel is byte-identical between BOOT, stock recovery and generated image; original compressed kernel payload SHA256 is recorded in the artifact manifest.
- Output MTK kernel/ramdisk names and lengths, Android boot ID, page alignment, load addresses and partition size are checked by reparsing the generated image.
- Newc archive is reparsed and compared entry-for-entry, including types, modes and the console device numbers.
- BusyBox ELF is aarch64 and its complete direct `DT_NEEDED` list is the included musl libc; the required bootstrap applets are present in the binary table.
- Shell syntax and Python compilation pass. Trace-parser controls accept ordinary and resumed successful completions and reject missing, failed, duplicate, unfinished and wrong-request evidence. Two rebuilds are hash-identical. These checks do not simulate the boot or qualify USB/mount/cold-WMT behavior physically.

The shell/sysfs/legacy-gadget approach is adapted from `kaantcp/z380m-alpine` commit7218a276f252a59874ab860683c061fa2b856519 under GPL-3.0-only, with attribution retained in the scripts. The donor's expdb raw logging, internal SYSTEM-root installer, ELAN assumptions and automatic GUI path are not used.
