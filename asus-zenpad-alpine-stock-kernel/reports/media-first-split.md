# Media experiment45 — 2026-11-08

Latest outcome: the owner heard the direct speaker tone. The later one-preference RDD fallback was tested and rejected, then removed. Both fixtures are stopped and normal portrait/dashboard startup is restored. Read [experiments46–47](media-second-result.md) before using any continuation advice below; the removed RDD candidate must not be reapplied.

Native Goodix scrolling, pinch zoom and automatic keyboard typing are physically qualified and survived an ordinary boot. This experiment leaves those settings in place.

## Browser result

The real owner Firefox140.12 profile played a locally generated H.264 baseline640×360,24fps video without an audio track. In the repeat after the fixture deadline fix, playback reached9.993seconds with240total frames and7dropped frames. There was no media error. This proves a modest video workload, not YouTube or higher-resolution playback.

The same video remuxed with a quiet48kHz AAC track fails even while muted: currentTime stays0, HTMLMediaError code3, and Firefox logs `NS_ERROR_DOM_MEDIA_REMOTE_DECODER_CRASHED_UTILITY_ERR`. A signal-only trace observed the new decoder process terminate with SIGSYS; the last trap was `tkill`, after many brokered `openat` traps. That last syscall may be secondary to the underlying failure; it is not yet a root-cause diagnosis. No sandbox setting was weakened.

The browser was closed normally, followed by exact-owner TERM when it lingered, with profile SQLite quick_check=ok. It was restarted on the same shared D-Bus/XI2/Onboard session with diagnostic-only `MOZ_SANDBOX_LOGGING=1` and `MOZ_LOG=PlatformDecoderModule:5,FFmpegAudio:5`. This environment is runtime-only and is absent from persistent browser startup. Loader diagnostics show FFmpeg61 loading many shared dependencies in the utility process. ENOENT in loader search paths and denied `/usr/local/lib` fallback searches are not by themselves the fatal cause. Root has over1GiB free; RAM tmp/shm were nearly empty before this test.

The original fixture awaited a play promise that remained pending after the decoder error. Its host observer timed out its readiness check; it did not change the tablet input path. The fixed fixture applies a five-second play deadline and remains bounded to15minutes on loopback8083. Synthetic samples contain only generated testsrc2 imagery and a440Hz tone, with no downloaded/private media.

## Speaker route result

[Stock audio audit](stock-audio-route-audit.md) identified the OEM XML route. Actual controls match that driver, with both amp gates initially off. `/proc/config.gz` is absent. Runtime `Audio_Speaker_class_Switch` / `Audio_Speaker_PGA_gain` controls are compiled only under CONFIG_MTK_SPEAKER in the matching OEM source, providing branch evidence. The loaded OF codec node identifies `mediatek,mt8163-soc-codec-63xx`, `extspkamp-gpio` resolves to the MT8163 pinctrl controller, GPIO28,flags0. No userspace GPIO pulse or calibration operation was used.

A single bounded `hw:0,0` stream completed at S16_LE stereo48000Hz, period2304frames, buffer9216frames. It contained one second of faded440Hz at-40dBFS, surrounded by silence. The helper prepared PCM, selected0Db and CLASSAB, enabled Speaker then Ext, and disabled Ext before Speaker on completion. Both switches read back off, PCM closed, original gain/class restored, no cleanup errors. An independent six-second shutdown guardian also ran. This is electrical/software route evidence; audibility is pending owner feedback.

The visible loopback page offers “Play quiet speaker test” using the same helper and same fixed signal. Requests require a page-specific token and exact loopback Origin, with a ten-second repeat interval. It does not increase gain or run calibration. Its15minute server exits automatically. Do not confuse this direct ALSA test with Firefox decoded audio playback.

Only ALSA diagnostic packages were added under `.asus-audio-tools`; prior APK world is saved at `/etc/apk/world.asus-before-audio`. No audio boot service, persistent mixer state or ALSA default configuration was installed. Recovery/BCB, stock firmware/calibration and input markers were untouched.

Sanitized result: `evidence/media-first-split.json`. Raw bounded observations remain ignored in `private/live/media-*` and `speaker-tone-first-proof.txt`. If continuing after the page expires, first verify server PID/status; do not rerun the stale-directory-refusing start helper blindly. Diagnostic logging applied only to that browser process, not persistent startup.

Update: **the owner heard the quiet tone**, physically qualifying this direct speaker route. The media server was stopped cleanly before the landscape trial, with both amps off and PCM closed. That desktop restart returned Firefox to normal logging. Browser decoded audio is still unresolved.

Opus5.5's completed report is opus-media-utility.md. Read-only device checks found zero sys_membarrier symbols and no sandbox-violation/assertion/terminate phrase in the full diagnostic log. These fit the proposed post-sandbox musl TLS/membarrier fallback crash but do not yet prove the final tkill arguments. The next diagnostic can capture membarrier/tkill/tgkill once after the physical landscape trial. A removable one-preference RDD compatibility policy is prepared at overlay/goodix/etc/asus-goodix/firefox-rdd-compat-policies.json; it is **not installed**. FirefoxESR140 policy source explicitly permits the media. prefix. If used, audio/video would share the existing sandboxed RDD process, retaining audio exclusion from content, with less compartmentalisation than the default separate audio utility process. Verify Seccomp2 and actual muted AV playback before unmuted output. No policy or decoder-routing change has been applied.
