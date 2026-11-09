# Paused state and safe continuation

Paused on2026-11-09 at the owner's explicit request. Do not automatically resume hardware experiments from this archive. The original working folder and all excluded private inputs remain on the owner's Mac at `/Users/kahtaf/Documents/workspace/ideas/2026-11-08-asus-alpine-stock-kernel`. The public archive is `asus-zenpad-alpine-stock-kernel/` in `Kahtaf/research`.

## Last verified running state

Alpine3.24.4/aarch64 on exact stock Linux3.18.35; native portrait800x1280; Firefox showing the local dashboard; native Goodix/libinput and Onboard; key-only Wi-Fi SSH; safe owned PulseAudio idle/SUSPENDED; both speaker amp switches Off. The final performance-session dashboard had85 saved requests and85% battery/Charging. These are historical observations, not a fresh device-health or battery claim at future resume time. Pausing did not shut down, reboot, reconfigure or restore the tablet. No timed physical trial or delegated worker is pending.

Normal startup is independent of the Mac. The persistent system is the mounted2GiB ext4 loop file `/mnt/alpine-sd/2026-11-08-asus-alpine/alpine-root.ext4`; /dev,/run,/tmp,/dev/shm are RAM. The SD root and browser/profile data remain private and are NOT published. Never copy this mounted image as a consistent backup, resize/detach it live, or mount it concurrently from a second system.

The latest UI work only enabled Firefox reduced motion. Xfce, LXQt, Phosh, Termux and Termux:X11 have not been installed or qualified as replacements. Native gestures and automatic keyboard were owner-confirmed earlier; landscape, buttons and browser audibility have no such acceptance.

## First actions if the owner resumes

1. Read this file, README.md, MEMORY.md, UPSTREAM.md and reports/INDEPENDENT-USE.md. Historical CURRENT/BLOCKED/NEXT statements in old reports are experiment history; this pause checkpoint and latest memory supersede them.
2. Locate the original local spike and private rollback/calibration/SSH material. A Git clone alone cannot reproduce the installed tablet. Do not invent credentials or weaken host-key checks. The original local `private/standalone-ssh.json`, key and known-hosts file are the control context; never publish them.
3. Inspect the actual device state through bounded, pinned SSH using `scripts/standalone-ssh.py`. If an ordinary Linux reboot produced a new boot ID, use the reviewed `scripts/bind-next-sd-boot.py`, which authenticates the retained host key and checks stock kernel/root/BCB. A failed guard is a reason to inspect, not bypass it. USB is fallback; the physical port is loose and rotating the tablet can disconnect it.
4. Agree which experience to pursue: one reversible native Xfce session on the existing Alpine/WMT/input/audio base, or Android's interface with Linux tools alongside it. The fresh research favors Xfce as the native trial, but neither route is a proved improvement on this tablet yet. Do not install several speculative variants.
5. For native continuation, complete on-device settings and button actions, ordinary sound and service recovery, then qualify cold shutdown/power-on when physical recovery is available. Keep sensor/MD32 activation and new kernel/Android porting parked. See the exact acceptance gaps in INDEPENDENT-USE.md.

## Internal storage and rollback

Only recovery p10 and the documented BCB selection fields were deliberately changed. Original BOOT, SYSTEM, GPT, bootloader and factory data were not replaced.

- Original BOOT SHA256: `7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316`.
- Installed stock-kernel Alpine recovery capsule SHA256: `097ea7b81f4c3e847d5aec34834b404b70db7db945031be9082946b922f08a6c`.
- Canonical stock recovery SHA256: `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`.
- Selected BCB is `boot-recovery` padded to2048bytes with empty arguments; SHA256 `7b3d5382b8a753269520c60f01124f5dcea1a3c2e2e8c304623a46df79d046aa`.
- Clean all-zero2048byte BCB SHA256: `e5a00aa9991ac8a5ee3109844d84a55583bd20572ad3ffcd42792f3c36b183ad`.

Canonical Mac rollback images remain in the sibling `2026-11-06-asus-local-stock-rollback/artifacts/stock-rollback/`. Stock recovery is additionally retained in the tablet's marked SD private folder. Factory calibration and radio firmware dependencies are local only. Do not delete these while keeping only the Git archive.

Avoid the physical boot-menu Recovery branch: exact LK analysis found it writes wipe arguments. NEVER restore the older pre-cleanup BCB snapshot. The qualified stock-return state has empty recovery arguments. See reports/OPERATING.md for the guarded command-only utility and its exact qualification limits. Android startup restores stock recovery, so returning from Android to Alpine needs a freshly guarded reapply of the proven capsule. No self-contained dual-boot selector was established. Do not blindly rerun historical installers.

## Runtime hazards to retain

- Never rerun the WMT loader on a warm kernel. Readiness requires successful module-init ioctl0x80047704 plus stpwmt registration; loader exit255 can be a property-service failure. Preserve original firmware and private calibration; no chip-ID override.
- Stock ALSA PCM data mmap caused a real kernel oops. Preserve the bare-hw fallback guard and the owned PulseAudio mmap=0 route. Never run the default PulseAudio scripts or old direct browser-sound fixture. Keep the app-private FFmpeg libraries and sandbox defaults.
- Speaker-check is manual and bounded. It does not enable normal desktop sound. The speaker controller is a separately qualified prototype, not an always-on audio service.
- Do not activate MD32, write accelerometer controls, use gsensor ioctls or read calibration callbacks. Matching2018 source and a reversible hub lifecycle are missing.
- Preserve the current Firefox profile/history. Close the exact owner normally, using TERM for its lingering parent if needed; do not SIGKILL/delete the profile. Preference rollback can require resetting values persisted in prefs.js.

## Archive limitations

This is a reviewed selection of authored/adapted source, patches, notes and small sanitized evidence. No runnable installation or private input is promised by clone alone. Most scripts record one experiment's preconditions and may refer to excluded local staging. Scripts are archived without executable Git modes; explicit interpreter execution can still perform writes, so review each before use.

SOURCE-PRESERVATION.json records upstream origins and selected hashes. BUILD-INPUTS.md lists intentionally missing inputs. ARCHIVE-MANIFEST.json covers the published files; `python3 tools/check-archive.py` performs an offline size/content/integrity check. No large artifact upload, Git LFS migration, OS replacement or hardware experiment accompanies this pause.
