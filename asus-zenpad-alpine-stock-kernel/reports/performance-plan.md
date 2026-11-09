# Performance baseline and first change

The current idle desktop is already small. One six-second observation showed about98% aggregate CPU idle,0% I/O wait and1,429,676KiB available memory of2,000,192KiB total. This is an idle snapshot, not a scrolling, startup, busy-site or storage benchmark. The collector initially skipped processes because `/proc/PID/io` was unavailable; the corrected collector made I/O optional. Its zero per-process I/O fields mean unavailable, not measured zero. Do not infer a disk bandwidth or speedup from these runs. Stock load average was about7 despite idle CPU; do not interpret it as seven busy CPU cores.

Only one CPU was online at idle, but two short CPU workers caused stock `hps_main` to bring CPU1 and CPU2 online automatically. Both workers completed successfully. No CPU/governor/hotplug/thermal controls were written. Pinning all cores online is not justified by this evidence.

The display uses Xorg fbdev with a software shadow framebuffer. The root is ext4 with noatime; /tmp,/run,/dev/shm are RAM, Firefox disk cache is already disabled and autoplay is blocked. No swap is enabled and current memory is abundant. Keep the small JWM desktop, native input, shared accessibility bus and safe PulseAudio route. Do not disable required input/accessibility or sandbox components to trim process count.

## Applied change

Added only `ui.prefersReducedMotion=1` to the actual Firefox default preferences. This requests less decorative browser/page motion; it does not force a GPU driver or change APZ/native touch, process isolation or decoder sandbox settings. The source overlay was also brought in sync with the already-installed crash-resume/autoplay preferences, which were missing from that local source file.

The owner profile was closed normally with the existing exact-owner procedure, with TERM only for a lingering parent. Closed places.sqlite quick_check passed with23 retained entries. Firefox restarted as4603; no profile/history was deleted. A temporary loopback page in the actual browser observed matchMedia(reduce)=true, its respecting CSS animation=none, a real requestAnimationFrame callback and a successful dashboard fetch. The fixture stopped and Firefox returned to the normal dashboard; the same owned PulseAudio2479 was SUSPENDED. No overall speedup percentage is claimed. Physical touch was not rechecked while the owner is away.

Preimage and mode are saved privately on SD in `private/before-reduced-motion/`. To undo, restore that default file and remove the single ui.prefersReducedMotion preference from the CLOSED profile's prefs.js/user.js, or reset it in about:config; merely deleting it from the defaults will not clear an already-persisted profile preference. Preserve every other preference. Restart through the normal profile-preserving launcher.

## Priorities

1. Reduce work loaded by real sites: assess one maintained content blocker and Reader View on representative useful pages. This is a proposed next experiment, not an installed extension or measured gain.
2. Start video at modest resolution, then raise it only if playback remains responsive. Do not force experimental hardware decoding or change the qualified audio bridge.
3. Keep heavy builds and computation on the Mac, with small tablet services. Avoid unnecessary dashboards that repaint/poll continuously.
4. Measure actual page interaction and cold application startup before considering storage changes. No SD purchase, unsafe ext4 mount options, SD swap, or moving profiles into RAM is justified by this idle snapshot.
5. Consider compressed RAM swap only if real multiple-tab workloads demonstrate memory pressure and the stock-kernel implementation can be qualified. It is not an idle-speed fix.

Mozilla documents the preference and how respecting pages reduce motion: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion . Firefox acceleration documentation is generic; it does not qualify the tablet's proprietary Android GPU stack: https://support.mozilla.org/en-US/kb/performance-settings .

Raw observations are ignored under private/live/performance-* and cpu-online-readonly.txt. Sanitized result: evidence/performance-baseline-and-motion.json.
