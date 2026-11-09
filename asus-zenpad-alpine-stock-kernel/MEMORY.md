# Current ASUS Alpine state

**PAUSED by the owner on2026-11-09.** The goal tracker is paused. This supersedes historical instructions to continue autonomously. No tablet experiment should resume until the owner asks. Read STATE-AND-RESUME.md first, then README.md, UPSTREAM.md and PROMPT.md. Detailed dated findings below are retained for a future continuation.

## Hardware and current access

ASUS Z380M/P00A_2 independently runs Alpine3.24.4 aarch64 on its exact original Linux3.18.35. Wi-Fi and pinned key-only SSH2222 are primary control. Current host/boot binding is ignored private/standalone-ssh.json; use scripts/standalone-ssh.py for bounded commands. Do not print private configuration or operate unrelated ADB devices.

Owner is away. Its USB port is mechanically unreliable; rotating the tablet can disconnect it. Keep it stationary, do not request cable handling or another timed physical check while unattended. USB is fallback only. No physical test can be accepted without actual owner evidence.

The latest landscape trial EXPIRED UNACCEPTED and returned to native portrait800x1280. Both REQUEST and persistent rotation marker are absent. It had no physical inputs. No trial is currently awaiting owner action.

## Critical source caveat and sensor branch

Actual stock kernel is Aug2018/firmware5.3.20; retained source is Jan2017V4.7.0 and is NOT exact running-driver source. Binary has SENSORHUB and a delayed calibration loader absent from that tree; no android_gsensor code. Old source-based show/store assumptions must not be reused. Previously qualified actual Wi-Fi/touch/audio workloads remain actual evidence; don't undo them solely for this source gap.

ACTIVE SENSOR WORK PARKED: no MD32 boot operation in Alpine, passive log has0retained matches and MD32 IRQ0/0/0 (consistent with inactive, not direct proof). No safe activate/sample/restore contract. Do not access md32_boot, write any accelerometer controls, call gsensor ioctls or read calibration/data sysfs. MD32 startup may reset hub calibration and is outside current qualification. Official ASUS listing tops out at2017V4_7_0; matching2018source not listed. See reports/sensor-hub-blocker.md. Passive observer source now uses input-core operations only. Native portrait/no rotation marker stays.

## Preserved system and boot guards

Root is a mounted2GiB ext4 loop file at /mnt/alpine-sd/2026-11-08-asus-alpine/alpine-root.ext4. Do not copy/replace/resize/detach it while mounted. Existing outer VFAT is protected root-owned nosuid/nodev/noexec; runtime /dev,/run,/tmp,/dev/shm are RAM. Stock SYSTEM is ro,noload. Browser profile and history remain private inside SDroot.

Original BOOT SHA2567bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316 is intact. Installed recovery is the proven stock-kernel capsule097ea7b81f4c3e847d5aec34834b404b70db7db945031be9082946b922f08a6c. Original recovery902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20 is backed up on Mac/SD. No BOOT/SYSTEM/GPT/bootloader/factory replacement.

BCB is exactly boot-recovery padded to2048bytes, SHA7b3d5382b8a753269520c60f01124f5dcea1a3c2e2e8c304623a46df79d046aa, empty recovery arguments. Clean stock BCB is all-zero SHAe5a00aa9991ac8a5ee3109844d84a55583bd20572ad3ffcd42792f3c36b183ad. NEVER restore the pre-cleanup snapshot containing wipe args, or select physical boot-menu Recovery (its LK branch writes wipe args). See reports/OPERATING.md.

Ordinary return to stock and repeat Linux boots are verified. Android restores canonical stock recovery, so re-entry needs guarded recovery-only reapply after fresh identity/hash/geometry evidence. Old installer scripts have differing preconditions; do not blindly rerun. The Android root helper applies ONLY after exact stock properties and Enforcing. Current live system is Alpine, not Android. Cold power-off/suspend are unqualified.

On a genuine later Linux boot, scripts/bind-next-sd-boot.py authenticates prior host key and verifies new boot, stock kernel, SD root and exact BCB before rebinding. Never bypass host-key or boot guards. Never rerun the WMT loader on a warm kernel.

## What is qualified

- Stock WMT cold startup exactly once per kernel boot, successful module-init ioctl0x80047704 plus stpwmt registration, stock-format ready property and original firmware/private WIFI calibration. Loader exit255 is failed Android property_set, not module failure. Standard device permissions follow mdev. No chip-ID override.
- Native wpa_supplicant2.11/DHCP/HTTPS/pinned SSH across boots. Actual resident-client DHCP renewal proved. Persistent dashboard SQLite/OS files and stable SSH identity survived boots and a stock Android round trip.
- Xorg21.1.25/fbdev/JWM/Firefox ESR140.12 auto-start. Goodix GT6108 direct16-contact libinput native mode owner-confirmed for tap/scroll/pinch/type. Canonical event path is mandatory; metadata is truthful and needs no udev daemon. Old pointer bridge retained as fallback. Marker native-touch=libinput-v1; Firefox MOZ_USE_XINPUT2=1. maxTouchPoints=0 is not a valid failure gate in this ESR build.
- Onboard automatic bottom keyboard physically typed tablet and ok, hid on Done. Separate asus-jwm workarea fix shrinks Firefox above280pixel keyboard and preserves geometry; packaged jwm unchanged. Shared D-Bus/AT-SPI required. Marker automatic-keyboard=onboard-v1 and jwm-workarea=jwm-2.4.6-workarea-v1.
- Browser normal stop preserves profile, no SIGKILL; latest closed history quick_check=ok/19entries. Native input and keyboard passed ordinary kernel boots. Software CW landscape1280x800 renders, but physical orientation/taps remain unqualified. No auto rotation; do not touch accelerometer gs_cali/resetcali attributes (reads mutate calibration).

## Media and current audio lifecycle

Experiment49 installed app-private TLS-free FFmpeg61/avutil59 under /usr/lib/firefox-esr. AAC decode passed with isolated Utility/Seccomp2; system libs/prefs/sandbox unchanged. Exact hashes and rollback: reports/private-ffmpeg61-result.md. Preserve qualified files.

A separate unmuted output attempt exposed the original vendor DL1 broken .page callback: hardware data MMAP causes snd_pcm_mmap_data_fault kernel oops. Recovered through verified stock Android, held GUI, reapplied SAME recovery only, kept BCB byte-identical, returned to Alpine. Why LK selected Android after panic is unproved. Never test the bad MMAP path again.

Experiment50 fixed OUTPUT with a bare-hw /etc/asound.conf fallback guard and owned PulseAudio17 serial sink hw:0,0 mmap=0 tsched=0 S16_LE/48000/2. Actual unmuted browser playback passed9.75s/235frames/4drops/errornull; no Firefox hardware PCM fd/map, UtilitySeccomp2, ampsOff, no kernel oops. Desktop starts owned audio before Firefox and stops it on exit. This integration passed an ordinary kernel reboot. Default PA scripts must NEVER execute. Do not remove the fallback guard or enable broad Firefox decoder preferences.

Experiment51: real muted YouTube sample M7lc1UVf-VE played15.80964s/qualitylarge, no player/API/autoplay error, all playing samples muted. Observer stopped and dashboard restored. This is one stream, not physical audibility/all-video qualification.

LATEST52: module-suspend-on-idle timeout=5 now closes PCM on idle. Owned helper validates SUSPENDED+closed or exact native RW hardware parameters owned by its PulseAudio process. Real same-daemon idle→unmuted Firefox9.624687s/232frames/4drops/errornull→idle passed; hardware closed before/after, amps off throughout, Firefox no hardware PCM fd/map, no new oops. This revision passed desktop restart, not another kernel reboot. See reports/audio-idle-result.md, evidence/audio-idle-lifecycle.json; preimages SD private/before-audio-idle. Idle suspend does NOT disable amplifiers.

Owner heard a quiet DIRECT ALSA speaker tone earlier. Browser audibility remains unconfirmed. Both amplifier switches currently stay OFF; no persistent automatic amplifier controller/global UCM route is enabled. Standard idle-suspend closes PCM but doesn't run UCM DisableSequence. Next work: source-reviewed automatic speaker lifecycle with reversed shutdown and independent cleanup, before enabling a persistent route. Existing browser-sound fixture predates PulseAudio and must not be run unchanged (it expects Firefox to own PCM).

## Latest53: automatic speaker prototype

Separate bounded G/C prototype passed both actual episodes on the same PulseAudio: normal observed-IDLE→ExtOff→SpeakerOff in0.145s while PCM open; SIGSTOP injection→heartbeat expiry about2.50s→group kill/reap→orderedOff byREADY+2.99s while PCM open. Class/gain0/1 restored, preimage deleted, lock released and group gone after each. Both browser AAC plays ended3.021333s/errornull. Final gatesOff/PCMclosed/no new oops. See reports/speaker-lifecycle-result.md and evidence/speaker-lifecycle-result.json. Prototype remains separate; physical browser audibility is unconfirmed and no persistent amplifier route is enabled. Do not run old browser-sound-trial route implementation. Continue independent work while physical confirmation is deferred.

## Latest54: dashboard power indicator

Dashboard /health now includes power {battery_percent,battery_status,usb_power_connected}; HTML shows a compact battery/charging/USB POWER line. Actual83%/Charging/USBpowertrue matched read-only standard sysfs attributes. Data count preserved across a dashboard-only service restart; source and consistent SQLite backup saved SD private/before-dashboard-power. USB power is not USB data continuity. No timer or extra polling. See reports/dashboard-power-result.md. Accelerometer investigation continues read-only; fresh bound driver is BMA255 at I2C2-0011, m_acc_input event6, m_acc_misc10:34. Do not read calibration attributes or activate until source contract allows reversible state restoration.

## Latest55: stationary accelerometer observation

Passive source-reviewed evdev read got0events/0fresh frames in3.002662s; cached axes0 are NOT fresh. Pure cpsopmode read stayed2 before/after. No sensor activation/delay/mode/calibration write or display change. Actual BMA255 driver attrs found under platform gsensor; android_gsensor absent and running config unavailable. Active sampling lacks truthful reporting/polling/delay/hub baseline getters. See reports/stock-accelerometer-sample-contract.md and accelerometer-passive-result.md. Historical question before the now-completed Opus rejection: whether exact driver init plus exclusive qualified Alpine startup can establish a provable initial state for a reversible bounded sample. Do not activate blindly or treat power2 as a full baseline. Continue other scoped work while this source question is unresolved.

## Latest56–57: sensor parked, manual speaker check ready

Passive MD32 log snapshot:0matching retained lines, IRQ0/0/0; consistent with inactive, not proof of reset state. Never access md32_boot or activate sensors. Official ASUS source catalog offers2017V4_7_0 and older, not matching2018source. See reports/sensor-hub-blocker.md. This is a sensor-specific blocker, not loss of Alpine/SSH.

Apps → Speaker check is now installed ON DEMAND. It starts a loopback8089server for15min only when launched; a deliberate Play quiet tone click starts the exact qualified six-second G/C prototype with immutable three-second AAC. Nothing autostarts or permanently enables amps. Files are /usr/local/bin/asus-goodix-speaker-check, /usr/local/libexec/asus-speaker-route-prototype.py, /usr/local/share/asus-goodix/sound.m4a; original prototype and media hashes retained. Initial non-actuating smoke passed page/media/headers/auth rejection/server reuse;0episodes/no mixer changes. A subsequent full-path software check ran exactly1bounded quiet episode successfully. Server is STOPPED, dashboard restored. New UI's positive arm/play subsequently PASSED one software cycle: trusted button→browser ended, normal orderedOff atREADY+3.543s whilePCMopen, class/gain restored, samePulse, then PCMclosed/serverstopped/dashboardrestored. Physical audibility alone awaits owner use; don't launch another timed physical prompt while away. Owner can use the menu while keeping tablet stationary, with no Mac operator/USB handling needed. See reports/on-demand-speaker-check.md and evidence/on-demand-speaker-check-smoke.json. Menu/source preimages SD private/before-speaker-check-menu; /etc/jwm corrected0777→0755 (old mode recorded). No boot/config/API changes beyond this menu/new manual files.

## Boundaries and continuation

Keep owner profile/history, keys, calibration, firmware and raw device logs out of Git. Original donor unchanged at7218a276f252a59874ab860683c061fa2b856519; do not run its BOOT/SYSTEM installer. Android17, Linux4.9 and new GCP resources remain parked. No new physical trial until owner available with suitable handling. Continue independent implementation/qualification over Wi-Fi.

Prior detailed chronological memory is archived in reports/MEMORY-through-experiment51.md; old CURRENT/BLOCKED statements there are historical, not live instructions. Evidence and correction reports remain authoritative for their specific experiments. Goal is not complete.

## Latest58: performance baseline and reduced motion

Idle snapshot~98% CPU idle,~1.36GiB available,0% iowait; not a loaded-page benchmark. Stock hps_main correctly onlines secondary CPUs under two short workers, so no CPU/governor controls changed. Display is fbdev shadow software path. Added ui.prefersReducedMotion=1 to actual default and aligned source overlay with already-installed crash/autoplay prefs. Normal browser restart preserved closed history quick_check=ok/23entries; new parent4603. Actual page matchMedia(reduce)=true and respecting CSS animation=none; RAF+dashboardfetch passed. Probe stopped/dashboard restored/same Pulse2479 SUSPENDED. No overall speedup claimed, no physical touch recheck. Private SD backup before-reduced-motion; reset persisted profile preference too when rolling back. Next candidate is one content blocker/Reader View on real useful pages; none installed yet. See reports/performance-plan.md and evidence/performance-baseline-and-motion.json.

## Latest59: independent-use readiness audit

Owner asks for everyday independence and power/volume/Bluetooth status. Passive live audit: mtk-kpd event1 advertises KEY_POWER/KEY_VOLUMEUP/DOWN; no physical presses verified and no JWM/button-controller actions configured. Xorg auto-add=false. No sys/class/bluetooth/HCI/stpbt nodes, no BlueZ tools; BT not brought up. No hardware activation or settings changed. Wrote reports/INDEPENDENT-USE.md and evidence/independent-use-hardware-audit.json. Minimum next milestone is on-device controls plus button blank/wake/softwarevolume, ordinary speaker integration, service recovery, then owner-available cold shutdown/power-on verification; keep Bluetooth/rotation separate. Existing microSD system runs without Mac at runtime, but cold power/suspend and full consumer-tablet behavior remain unqualified.

## Latest60: owner wants polished functional tablet, not minimal bring-up

Research completed in reports/interface-recommendation-2026-11-09.md. Native recommendation: one reversible Xfce-on-Alpine trial, compositor off, preserve WMT/input/Onboard/audio and JWM fallback; not yet installed/tested. LXQt is second, no measured RAM advantage. Phosh needs an unqualified Wayland/display/device route; Plasma mainline-only; UbuntuTouch Z380M absent from official list; Droidian requires Android9 base not established. Sxmo manual/menu UX poorly matches owner preference. Practical hybrid candidate: stockAndroid7 + Termux/Linux tools, optional Termux:X11/Xfce. Current official docs support Android7 for both; not installed, no speed/compatibility claim. Do not switch OS or reuse/mount native SD root twice as a side effect of research. User request to find alternatives does not resume Android17/4.9 or authorize speculative device ports.

## Latest61: explicit owner pause and Git archive

Owner requested pausing and committing resumable source/docs to Kahtaf/research without large artifacts. Goal is paused. No tablet command, reboot or hardware write was sent during archival. Source-only export includes authored/adapted code, small evidence, upstream pins and STATE-AND-RESUME.md; private data, images, firmware/calibration, fetched trees and builds remain local. Xfce/hybrid alternatives remain recommendations, not installed changes. Public scripts are historical reference material, not an installation batch.
