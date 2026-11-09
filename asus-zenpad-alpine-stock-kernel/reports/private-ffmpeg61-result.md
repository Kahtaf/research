# Experiment49: isolated Firefox H.264/AAC playback passes on stock3.18

2026-11-08. The browser-private, TLS-free FFmpeg61 build passed the real tablet's fresh-parent H.264+AAC test, retaining the separate audio utility process and seccomp2. Physical browser audibility and YouTube are still unverified.

## Build and actual gates

The existing local AArch64 Docker builder used pinned Alpine digest `f59abe656b692d901e184be3445e084786602108599d2a51d229c0f5a48c71bf`, limited4CPUs/4GiB. The disposable container was removed. Only public source/staging and its output were mounted. No cloud resource, new VM or tablet compiler was used.

Unpatched FFmpeg7.1.5 source SHA256 `de668509caf9e35e3cd162473441fdb29538c6d96ed080292b3cf9e6fc5d558f`. Rebuild script `scripts/build-browser-ffmpeg61.sh`; complete source/configuration/license/compiler logs and validation outputs under ignored `artifacts/browser-ffmpeg61/`. LGPL decoder-only AAC,H264,HEVC,VP8,VP9,VP6F; Firefox's bundled ffvpx continues to provide its other codecs. Encoding and unavailable hardware acceleration are not supplied by this browser-local bundle.

The two regular output files passed ELF64/AArch64, exact SONAME, noPT_TLS/TEXTREL/RPATH/RUNPATH, exact dependencies, all41 mandatory v61/version exports, bare-soname RTLD_NOW|LOCAL load and decoder discovery. The harness's entire new closure is avcodec, avutil and existing musl. On the retained actual elementary streams, decoding matched the reference extent:288H264frames and577536AACsamples/channel. Pixel/sample equality was not asserted. HEVC/VP8/VP9/VP6F have discovery coverage only.

| Installed app file | SHA256 |
|---|---|
| `/usr/lib/firefox-esr/libavcodec.so.61` | `9435c2bd290a63b33d74dde2c366af9bf12bb2916ef47e637619e41caecbf96f` |
| `/usr/lib/firefox-esr/libavutil.so.59` | `0554838b786e990a4155557fd1103c178adf54a7a143f4947917294f01e5fc36` |

Only these previously absent app-local files and `/usr/lib/firefox-esr/asus-ffmpeg61.json` were added. Original `/usr/lib/libav*` hashes matched before/after. No browser preference, filter, environment search override, profile or kernel change selected the bundle; Firefox's existing app-directory search and broker allowance selected it. It persists in the SD OS root. Ownership/preimage receipt is privately saved in SD `private/firefox-before-private-ffmpeg61`.

## Real playback result

A fresh parent start on the same preserved owner profile loaded the local fixture once. Video-only reached9.985708seconds/240frames. The formerly crashing H264+AAC stream reached**9.86108seconds,237frames,0dropped,error=null** while muted. The utility process was still live when inspected, with Seccomp2 and both app-local libraries mapped. Systemavcodec/util and gomp/numa/jxl_cms/soxr/x265 were absent from that utility mapping. Actual Utility FFmpegAudio logs showed decoded AAC samples. No decoder-crash/error remained.

This supports the TLS-dependency explanation by intervention; the exact former membarrier/tkill sequence has still not been directly observed. Do not claim that unobserved syscall trace was obtained.

The manifest was marked `qualified-decoding-on-stock-3.18.35`. Firefox then closed normally/exact-owner TERM; profile quick_check passed with15retained history entries, and normal dashboard startup resumed with XI2/Onboard and no diagnostic logging. Both previous fixtures stopped. A separate silence-only default-ALSA preflight proved ordinary `default` reaches PCM0,S16_LE,48kHz,stereo,period2304/buffer9216; both speaker amp gates stayed off and PCM closed.

Rollback helper `scripts/remove-private-firefox-ffmpeg.sh` verifies the exact owned files/manifest before deleting them, then requires a fresh browser restart. It is reviewed, not executed after this positive qualification. Removing/reinstalling the same passing files was not repeated. Future Firefox/FFmpeg upgrades need a new ABI/selection check; a newer systemavcodec62 would supersede61 and this bundle would no longer be selected.

Sanitized evidence: `evidence/private-ffmpeg61-playback.json`. Raw proof/build/profile outputs remain ignored under `private/live/private-ffmpeg-*` and artifacts/.

## Current access blocker and unfinished workload checks

Before navigation tooling could be staged for the actual YouTube check, LANSSH began timing out. This Mac's fresh USB inventory has no ASUS device and no USBmodem port. The tablet's saved address still returned two ICMP replies, and ARP matches its previously recorded station MAC. Therefore this is an unavailable control path, not evidence that Wi-Fi association failed or the tablet powered off. No reboot, loader rerun, rollback or network mutation was sent.

The first YouTube observer stopped at a startup window-readiness guard before browser navigation. YouTube playback is **not tested** after the fix. A shared readiness helper is now prepared at `overlay/goodix/bin/goodix-open-url.py` and used by current trial sources, but its SCP failed; it is **not installed** on the tablet. Stage it after access is restored before using those updated trial scripts. The last normal browser parent observed was4900; revalidate the profile lock before acting.

`scripts/browser-sound-trial.py` and ignored `artifacts/browser-sound-trial/` are prepared offline only. Its immutable3second AAC clip contains the same one-second faded quiet tone, decoded peak-39.886dBFS. It arms the stock amp route only on a trusted page click, with exact browser identity, origin/token checks, ordered cleanup and independent deadlines. It has **not been staged, started or physically heard**. No persistent audio service or idle amp lifecycle was installed.

Smallest next action: reconnect ASUS USB to this Mac, then identity-bind the console and inspect the existing boot, DHCP/WPA state and SSH listener/process before any restart. Preserve volatile evidence; never rerun WMT loader on a warm kernel. The owner has been asked to reconnect USB and report the screen state. This is the first turn with this access blocker; goal remains active.
