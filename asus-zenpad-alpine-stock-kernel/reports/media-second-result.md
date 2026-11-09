# Experiments46–47: landscape rollback and rejected RDD fallback

2026-11-08. Same pinned independent stock3.18.35 SD-root boot. No recovery, BCB, kernel, firmware, factory calibration or partition operation.

## Physical speaker output is qualified

The owner tapped the quiet direct-ALSA test and explicitly heard its short tone. The route is the OEM CLASSAB→Speaker→Ext sequence,0Db,48k stereo, one-second-40dBFS signal. Both gates returned off; PCM closed. This does not qualify decoded browser sound or arbitrary volume levels. No audio route is persistently enabled.

## Landscape software gate and automatic portrait restoration passed

The reviewed fbdev CW option and matching native-libinput matrix produced a1280×800 root, direct16-contact touch class and visible landscape Firefox. Browser screen1024×640 is correct under the existing1.25scale preference. A strict DOM physical-pixel assertion was corrected; physical root geometry remains the display gate. “ASUS landscape trial” was the actual window title.

No owner touches were recorded in the six-minute readiness window:0corner targets,0contacts,0scroll/typing. Therefore physical touch mapping, keyboard position and scrolling performance in landscape remain **unqualified**. Watchdog2130 completed `RESTORED_NATIVE_PORTRAIT`, the RAM REQUEST was removed, and actual root800×1280/native16-touch passed. No persistent rotation marker was installed. The landscape fixture has stopped.

Original helpers are privately backed up on SD under `private/desktop-before-landscape`. Initial desktop stop left an X socket/lock after its server had exited. Fresh `/proc` and `/proc/net/unix` proved no X server/socket owner; only the dead root-owned artifacts were removed. Desktop cleanup now gives Xorg up to5seconds to finish instead of killing after0.2, and Firefox is excluded from SIGKILL. The subsequent watchdog restart restored portrait without a stale-socket failure. These live userspace changes persist in SD root; no-marker portrait still uses the original rendering path.

## Audio decoder compatibility remains open

Read-only observations match Opus's TLS hypothesis: no sys_membarrier symbol, no sandbox violation/assertion/terminate line in the full loader log. A narrow reload trace yielded no tkill calls: after the initial failure retries, reloading did not launch a fresh audio decoder. This is **not** a negative test of the TLS hypothesis, and the precise fatal membarrier/tkill argument sequence remains unobserved. Any future capture needs a fresh parent launch under tracing, not another cached-failure reload.

The proposed removable default policy `media.utility-process.enabled=false` was then tested once. ESR140 accepted it and chose sandboxed RDD (Seccomp2). However, audio failed with the explicit error `NS_ERROR_DOM_MEDIA_DENIED_IN_NON_UTILITY`, “RDD is not allowed to perform audio decoding.” Source review located the missed second guard at `RemoteDecoderManagerChild.cpp:343`: it still requires `media.allow-audio-non-utility`, independent of track support. That broader preference also enables content PDMs, so it was not changed. No workaround that reduces audio isolation was retained.

The exact policy SHA1f7d6968b0846b1b7563054e95b04e412c42324486642d9861321445dce7c11e was removed. The rejected overlay candidate and installer were deleted to prevent accidental reuse; the negative result is retained in `evidence/rejected-rdd-policy.json`. Firefox was closed normally/through exact-owner TERM, profile quick_check passed with15history entries, and normal startup reopened the local dashboard with XI2/Onboard session environment and no diagnostic logging. The active media fixture was stopped cleanly. Both speaker gates remain off.

## Next bounded question

Preserve the separate utility decoder sandbox. Review whether a small browser-private FFmpeg61 decoding bundle without post-load TLS dependencies can avoid musl's barrier fallback, rather than a full Firefox rebuild. This is a source-review lead, not a selected implementation or another on-device variant. The original FFmpeg61 core libraries have no PT_TLS; reported TLS dependencies are encoder/resampler-side libgomp/libnuma/libjxl_cms. A bundle must retain real browser codecs/API, avoid changing system libraries, be allowed by the existing file broker, and prove no TLS in its complete closure. Otherwise the proper preload-before-utility-sandbox Firefox patch is the remaining route; state its actual build cost. Consult Opus on this exact failed proposal and one dependency-level lead before implementation. No Large fallback unless Opus refuses.
