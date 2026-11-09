# Initial Alpine experiment record — 2026-11-08

Later SSH, desktop, browser, SD and recovery-state results are in [CHECKPOINT.md](CHECKPOINT.md), which supersedes the provisional results below.

All tablet operations in this spike use freshly authenticated USB, exact stock identity checks and the retained on-demand root helper. Private raw outputs are under `private/live/`; public findings omit device/network identities and credentials. The donor checkout is pinned at `7218a276f252a59874ab860683c061fa2b856519` and unchanged. Official downloads still list stable Alpine3.24.4. Its aarch64 minirootfs SHA256 is `4b14c18f7e90a063b61462ea1462a5732c154bf6adad594974fe6487cd98a8de`, matched against the official checksum over HTTPS.

## 01 — Modern userspace on the actual old kernel

Prediction: a RAM chroot will execute current aarch64 BusyBox/apk and make an HTTPS transfer over already initialized stock Wi-Fi, without boot or filesystem replacement. Failure would isolate an ABI, routing or package problem.

Result: PASS. Alpine3.24.4, apk-tools3.0.9-r0 and BusyBox ran on Linux3.18.35 aarch64; HTTPS mirror-list download succeeded. Android tar could not find gunzip, so the identical checksum-verified archive was decompressed on the Mac and transferred as plain tar. RAM filesystem initially384MiB, later needs512MiB for desktop dependencies. This is a chroot, not an independent Alpine PID1 boot.

## 02 — Real packages and application libraries

Prediction: current packages can install and run against the stock kernel.

Result: PASS. Added43 packages including Python3, curl, OpenSSH, iw, wpa_supplicant and strace. Python ran OpenSSL3.5.9 and SQLite3.53.4; curl fetched the Alpine homepage over TLS. Initial package footprint69.4MiB. No kernel emulation was used.

## 03 — SSH service

Prediction: key-only SSH on LAN port2222 will execute a shell and SQLite/TLS workload. The daemon is automatically time-limited; no boot service is installed.

Result: NOT YET PASSED. OpenSSH listens, but Android Enforcing blocks re-execution of `/usr/lib/ssh/sshd-session` from the RAM filesystem (`Permission denied`). Subsequent attempted bounded root windows did not establish a successful session; do not attribute those resets to an OpenSSH/kernel incompatibility without a verified ready window and its logs. Ephemeral test keys and known-hosts stay private. Persistent SSH is not qualified.

## 04 — Native Alpine station control

Prediction: with Android station management stopped and stock WMT retained, native Alpine nl80211 supplicant can associate, get a lease through BusyBox udhcpc and transfer HTTPS. A trap stops the native process, removes its own metric42760 default route and re-enables Android Wi-Fi.

Result: PASS for native association/DHCP/TLS. Alpine wpa_supplicant2.11 reached COMPLETED using a private RAM copy of saved profiles; udhcpc obtained a lease; curl downloaded the homepage. The original stock WMT launcher stayed resident throughout. First attempt used unsupported `-f` logging option; corrected to shell redirection. No original network configuration was edited. This proves native Linux station tools, not stock WMT cold initialization.

Restoration: initial Android re-enable left the supplicant disconnected. Opus5.5 read the saved framework logs and identified `screenOn=false`, failed PNO scheduling and no ordinary network-selection scan. Saved networks remained enabled and scan results were fresh. Waking the display fixed it: stock supplicant COMPLETED, IPv4 lease present, HTTPS passed. Update future traps/preconditions to keep/wake the display and verify real connectivity, rather than merely a running daemon. Raw evidence: `experiment-04b-native-wifi.*`, `experiment-04c-awake-restore.*`, `android-wifi-dumpsys.txt`.

## 05 — Stock WMT runtime closure

Read-only private capture includes stock WMT loader/launcher, their Bionic interpreter/shared libraries, vendor firmware and the two existing calibration files. A private per-file hash manifest is retained. Both binaries use `/system/bin/linker64`; direct DT_NEEDED entries are libcutils, libc++, libdl, libc and libm. Resident maps additionally include liblog. No WMT loader was rerun against the live radio.

Result: NOT PASSED. A separate sealed compatibility subtree, without WMT nodes or `/proc`, launched stock `wmt_launcher -h` and exited136 (SIGFPE). This did not touch the original resident launcher. Exact runtime prerequisite is unresolved; do not claim that copying ELF dependencies alone solves standalone WMT startup.

## 06 — Goodix and desktop preparation

Fresh physical input inventory: goodix-touchscreen, typeB, live X0..800/Y0..1280, slots0..15, INPUT_PROP_DIRECT. Framebuffer virtual800×3840, visible expected800×1280, bpp32, stride3200. Donor ELAN ranges do not apply.

The Goodix overlay discovers by name and live ioctls, removes silent ELAN fallback, and provides a bounded display trial. Patched static aarch64 bridge built locally using Apple clang and the existing Rust LLVM linker; no toolchain download. Xorg21.1.25, JWM2.4.6, NetSurf3.11 and dependencies installed into RAM (367.4MiB package footprint). A subsequent index refresh hit the384MiB RAM cap; increase only this tmpfs to512MiB before further packages. Installation is not proof of rendering or browser usability. Desktop trial results will be appended after physical execution.

## Preservation and outstanding gates

No raw partition writes, bootloader/GPT changes, SD writes, factory reset, Android17/4.9 work or new cloud resources. Original rollback and factory archives remain untouched. Current recovery is still the retired diagnostic; its boot path and old SD triggers are not reusable blindly. Locked LK blocks assuming `fastboot boot`; standalone cold-start needs a concrete recovery/rollback-aware plan. Avoid rebooting until RAM work has been captured or deliberately discarded.


## 20–24 — Persistent OS file and first SD boot

Created one owned ext4 file on existing SD, using the exact legacy feature allowlist and real3.18 read/write mount proof. Increased from1GiB to2GiB before population because actual browser/profile usage justified capacity. Copied the closed OS and owner profile, excluding mounted SYSTEM/SD and runtime/private sidecar paths. Selected file hashes matched; unmounted/detached and e2fsck passed. Enabled root/GUI markers only after sealing. Recovery-only capsule update preserved its full preimage and passed cache-flushed full read-back; stock BOOT and BCB stayed unchanged.

Explicit stock-kernel recovery restart booted SD-loop PID1. Automatic cold WMT, native WPA/DHCP, stable-key LAN SSH, dashboard and Firefox passed. OS SQLite commit/read and HTTPS passed; request count15. A duplicate Browser launch could produce a profile-in-use prompt; the wrapper now validates and raises the existing profile owner. Actual execution retained its owner and raised Firefox. No profile was removed.

## 25–26 — Stock return and command-only Linux selection

Closed X windows, then used exact-profile TERM for Firefox's lingering parent; no SIGKILL. Ordinary reboot with the already-clean empty BCB returned to exact stock Android, stock3.18.35 and SELinux Enforcing. Android automatically restored canonical stock recovery902b2f06... . Reapplied the same already-proven capsule097ea7b8... and verified full read-back/original BOOT. Changed only BCB command bytes0–31 to boot-recovery, proving every suffix byte unchanged and recovery arguments empty. Root helper restored Enforcing.

## 27–30 — Two ordinary default Linux boots and real saved work

Both ordinary reboots reached the SD-loop Linux root without a recovery reboot argument. Each preserved exact BCB selection and authenticated the existing SSH host key. Cold WMT readiness, WPA COMPLETED, resident DHCP, HTTPS and visible Firefox dashboard passed. The original OS file and committed SQLite transaction survived the stock round trip and second default boot. Saved dashboard requests reached25. Owner browser files survived; a closed-profile quick_check passed with nine history entries.

A verification query of the live Firefox history hit its normal SQLite lock, so history integrity was checked only after browser closure. A boot observer initially saw the still-running old boot immediately after reboot dispatch; it now waits for a changed boot ID without requesting another reboot. These were observation issues, not repeated device experiments. No cold power-on, lease-renewal soak, suspend or full tablet UX qualification is claimed.

Installed boot-selection utility read-only status confirmed current Linux selection and original BOOT digest. Added a canonical stock recovery copy under the SD folder's private directory and verified its full SHA256. Goal remains active; deferred keyboard/gestures/rotation/media work and existing-mobile-layer assessment are recorded separately.


## 31–32 — Native Goodix XInput gate

Fresh live caps prove MT slots/X/Y/tracking IDs and DIRECT, but no legacy X/Y or BTN_TOUCH/FINGER. On a private dummy Xorg screen, evdev exposed a relative device without XITouchClass. Original desktop stayed running. Preserve the working pointer bridge until a revised bridge can retain MT with the necessary compatibility fields. No kernel driver replacement was inferred.

## 33–36 — Automatic keyboard and dynamic workarea

Stable Onboard/AT-SPI/D-Bus packages installed and Atspi import passed. A private-bus, temporary-profile Firefox fixture passed automatic bottom show/hide and actual Onboard key delivery via an XTEST click. Supervisor expired and cleaned its owned children. JWM published the strut but did not resize existing maximized windows; exact2.4.6 source established the missing reflow.

Fetched official MIT JWM source with the archive SHA512 matching Alpine APKBUILD, added the focused reflow correction, and compiled on the actual tablet under a120second bound with packaged features retained. Candidate789dbb... was promoted as a separate binary; packaged JWM remained107bd16... . Compiler dependency group was removed. Current SD UI enables the separate WM and shared D-Bus Onboard path; the old live helpers are privately backed up.

Normal owner-profile Firefox passed280pixel bottom docking, shrink/expand, restore geometry, automatic editable focus, actual Onboard a-key delivery and keyboard hide key. After correcting instrumentation focus/window-selection races, the owner physically tapped the field, typed tablet and hid the keyboard; all three worked, with browser event corroboration. Fixture stopped and browser returned to the persistent dashboard, count29. No recovery, BCB or kernel writes occurred for this UI integration. Kernel-reboot persistence of the new keyboard revision remains untested.

## 37–38 — Real resident DHCP renewal and final UI state

The client closes stdout/stderr to /dev/null when daemonizing, explaining why its initial log never showed later renewals. A trace limited to sendto/recvfrom missed connected-UDP read/write. Exact BusyBox1.37 source identified those calls; the corrected observation saw a genuine DHCPACK after SIGUSR1, the existing renewal hook updated resolver state, resident PID stayed unchanged and IPv4 was retained. Tracer detached. This proves one real renewal, not a long reliability soak. Private packets were kept out of public evidence.

Keyboard remains enabled on the normal desktop, with physical proof recorded. Gesture/rotation/media work remains active scope.


## 39–44 — Native Goodix/libinput and updated UI reboot

Existing libinput supports Android MT-only devices; metadata input_id recognized this panel without legacy buttons. Headless native probe exposed XITouchClass/direct16contacts, restoring metadata afterward. Production alias Device failed literal path matching; canonical-path runtime config fixed it. No custom multitouch bridge or kernel changes.

Browser maxTouchPoints0 was traced to ESR140 GTK's unimplemented base API, not device absence. Removed the incorrect API assertion without preference spoofing. Initial timed trial restored the pointer path before physical interaction. After owner reported the dashboard, a fresh trial began its six-minute window at actual page readiness. Owner then confirmed all3behaviors; browser recorded2contacts,1320pixels of scroll,3.218×zoom and ok through real touch. Accepted native mode stopped the watchdog.

Preserved owner history (quick_check ok,12entries), then ordinary-rebooted. Native16contact class, runtime metadata, automatic keyboard, FirefoxXI2, cold WMT/Wi-Fi, pinned SSH, persistent service and HTTPS all passed; dashboardcount41. No raw boot/recovery/BCB writes for input integration. RandR query separately established mask1/normal-only output; current display backend is the rotation gate. ALSA card/nodes were enumerated read-only; no sound route or calibration writes.
