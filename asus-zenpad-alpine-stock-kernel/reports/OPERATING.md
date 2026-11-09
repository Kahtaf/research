# Paused operating reference — 2026-11-09

The owner paused further work. [STATE-AND-RESUME.md](../STATE-AND-RESUME.md) is the authoritative handoff. Dated CURRENT/access-loss statements below are historical; use fresh guarded identity/boot evidence before any future operation. This archive is not a run-all installation guide.

# Operating the current microSD system

Manual speaker check: Apps → Speaker check opens an on-demand page; Play quiet tone runs one bounded three-second synthetic AAC through the qualified temporary route. Nothing plays on opening, no permanent speaker enablement, and no server at boot. The server expires15minutes after opening and each route is independently capped at6seconds. Keep tablet stationary; no USB movement is needed. If other audio is active, pause it and wait five seconds before trying. The new UI's full software click/playback/cleanup path passed; physical audibility remains owner-unconfirmed. Current server was stopped after non-actuating smoke, dashboard restored.

Automatic sensor rotation is parked: 2018kernel differs from retained2017source and needs an unqualified MD32/hub lifecycle. Do not activate sensor or hub, read calibration callbacks or rely on old driver sysfs show code. See sensor-hub-blocker.md.

Hardware handling: the owner reports a loose tablet USB port. Keep it stationary; rotating it can disconnect USB. Wi-Fi SSH is primary. Do not start another owner-dependent timed trial while the owner is away.

CURRENT experiment50 supersedes the Android/access blocker: guarded recovery-only re-entry restored Alpine3.24.4/stock3.18.35, with GUI initially held. Stock ALSA hardware MMAP is broken; a bare-hw fallback guard plus owned PulseAudio17 serial mmap=0 sink fixes actual unmuted Firefox output (9.75452s/235frames/4drops/errornull, utilitySeccomp2, no Firefox PCM fd/map, ampsOff). Desktop audio start/stop is integrated and passed another ordinary kernel reboot with Wi-Fi/SSH/native16-touch/Onboard/Firefox/dashboard58requests. GUI.ENABLE is restored. BOOT/SYSTEM/GPT/factory unchanged; same recovery capsule reapplied, BCB never changed. Browser audibility, idle power management and YouTube still open. Read reports/stock-alsa-rw-result.md (from reports/, stock-alsa-rw-result.md). Current pinned boot is in private/standalone-ssh.json. A fresh RAM-only landscape physical check is next; no persistent rotation marker exists.

CURRENT superseding earlier live/access statements: USB reconnect now reaches verified stock Android7, original kernel3.18.35, Enforcing, new boot. BOOT hash remains original; recovery is canonical stock. BCB remains exact command-only Linux selection with empty arguments. Retained prior-kernel log proves an oops in snd_pcm_mmap_data_fault from Firefox cubeb thread, followed by nested panic. No re-entry/reboot/partition write sent; no landscape trial is live. Hold media/landscape while a userspace-only mapping fix is reviewed. Read reports/access-return-kernel-oops.md (or access-return-kernel-oops.md from reports/). Old pinned Linux boot binding is stale.

The tablet is left running Alpine 3.24.4 on stock3.18.35, with Firefox showing the local dashboard. Ordinary reboots select the Alpine recovery capsule through a persistent BCB command. This selection survived two real ordinary boots. Physical cold power-off/on and suspend/resume are not yet qualified.

## Access and saved state

Use the pinned private connection in `private/standalone-ssh.json`; key-only SSH listens on port2222. `scripts/standalone-ssh.py SCRIPT --output private/live/NAME.txt --timeout 30` authenticates the saved host key and current boot ID. For a later ordinary Linux boot, first run `scripts/bind-next-sd-boot.py --output private/live/NEW-BOOT.json`; it accepts only a fresh stock-kernel SD-root boot authenticated by the prior host key and exact expected BCB. Never disable host-key checking to get around a failed binding.

The public authorized key is on the SD card; the client private key remains on the Mac at `private/alpine-trial-key`. Dashboard HTTP is loopback-only at `http://127.0.0.1:8080/`; use SSH forwarding to view it from another computer. SQLite dashboard data is bound from the card's marked `service-data` folder. Stable host keys are in its protected `private` folder.

Normal package/configuration files and the owner's browser profile persist in `/mnt/alpine-sd/2026-11-08-asus-alpine/alpine-root.ext4`. This2GiB file is the running OS root; do not replace, copy as a consistent backup, resize or detach it while mounted. Close Firefox and shut down through Linux before card removal. The file contains private profile/history, credentials and calibration copies; keep it out of Git.

Apps → Browser raises the existing Firefox profile owner. Editable focus automatically opens Onboard at the bottom. Apps → Keyboard toggles it manually. The owner physically verified typing and Done/hide. Firefox shrinks above the280pixel dock using the separate JWM workarea correction; packaged JWM remains available. Native one-finger scrolling and two-finger pinch are physically confirmed. Rotation and media remain open; see DEFERRED-UX.md and automatic-keyboard.md. Closing a Firefox window can leave the process resident on this stack. The project desktop-stop helper uses exact-profile TERM after normal window-close if needed, and checks closed history integrity; no profile files are deleted.

## Return to stock Android

Stock BOOT is intact and hash-verified. Selection is controlled only by the32-byte BCB command. The installed utility:

```
asus-alpine-boot-selection
```

reports the current selection without writes; this read-only mode was physically executed. To clear the known Linux selection and then reboot normally, close Firefox and run from authenticated root:

```
asus-alpine-boot-selection --return-to-stock --reboot
```

The source is `scripts/asus-alpine-boot-selection.py`. It verifies exact kernel/root marker, original BOOT digest, partition geometry and a known BCB preimage; privately backs up the current2048bytes; clears only command bytes0–31; syncs and checks every byte. Empty recovery arguments and reserved bytes stay unchanged. It refuses unfamiliar BCB contents. This clear mode is reviewed but has not itself been executed; the resulting empty-BCB stock-return path was physically demonstrated before enabling the Linux default.

An ordinary empty-BCB reboot returned to exact stock Android with SELinux Enforcing. Android's startup also restored canonical stock recovery automatically; that behavior was verified by full hash. Returning to Android can therefore remove the Alpine recovery capsule. Re-entering Alpine after such a return requires reapplying the proven capsule under the guarded stock installer, not assuming recovery still contains it. Do not blindly rerun historical deployment scripts: their exact preimage guards differ.

Original stock recovery is additionally saved at `/mnt/alpine-sd/2026-11-08-asus-alpine/private/stock-recovery.img`, SHA256 `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`. Canonical Mac BOOT/recovery/SYSTEM archives remain at `../2026-11-06-asus-local-stock-rollback/artifacts/stock-rollback/`. Restoring the recovery image manually is separate from clearing Linux selection; never install stock recovery while leaving a recovery command or wipe arguments active.

Avoid the physical boot-menu Recovery selection: its exact saved LK branch writes `recovery\n--wipe_data`. Use normal software reboot and the reviewed command-only selection path. Never restore the older pre-cleanup BCB snapshot, which contains the stale wipe request.

## Preserved fallback and boundaries

The earlier verified software archive and own markers remain in the dated SD folder. Removing only `ROOT.EXT4.ENABLE` while offline selects the capsule's768MiB RAM-archive path on a later recovery boot; it does not delete the ext4 OS file. The older archive predates Firefox, so this is a shell/recovery fallback rather than equivalent desktop state.

Only recovery p10 and the documented BCB fields were deliberately changed internally. Normal BOOT, bootloader, GPT, SYSTEM image and factory partitions were not replaced. Old SD rescue/Android17 triggers were not executed. No4.9 or cloud work is involved.


Native input is selected by `/etc/asus-goodix/native-touch` containing `libinput-v1`. Its metadata helper runs each GUI start; the Xorg template must receive the actual canonical event path, because xf86-input-libinput rejects Device aliases. No udev daemon is needed. To return to the proven pointer bridge, close the owned desktop through guarded SSH, rename just that marker to a disabled name, then restart from the guarded start helper. The bridge binary/config remain intact; no boot, recovery or BCB change is needed. Backups are in the SD private/desktop-before-native-input folder. Automatic keyboard remains enabled in either input mode.
