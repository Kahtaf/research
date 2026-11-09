# Deferred tablet usability work

Sensor-specific blocker: running2018SENSORHUB binary differs from the retained2017V4.7.0 source, and Alpine has no qualified MD32/hub boot/calibration-preserving lifecycle. Passive read gave no samples; active sensor work is parked. This does not block the working portrait desktop. See [evidence and missing contract](sensor-hub-blocker.md).

Latest51: muted YouTube sample now passes on the tablet for15.8seconds without player error after the decoder/output fixes. Browser audibility is still untested; the owner is away and no physical interaction is requested. See [actual result](youtube-muted-result.md).

## Current physical constraint

Owner is away. The tablet USB port is mechanically unreliable; physically rotating it can disconnect USB. Defer physical landscape/audio checks until the owner returns, and do not request rotation or cable handling while unattended. Keep the tablet stationary, use pinned Wi-Fi SSH as primary control and USB only as a recovery fallback. Landscape remains physically unqualified; leave the timed trial unaccepted and verify automatic portrait rollback. Continue bounded software checks without physical interaction.

The previous missing landscape page followed the ALSA kernel crash; experiment50 restored the desktop and fixed unmuted output through the guarded PulseAudio serial path. A later RAM landscape page loaded correctly in software but has no physical confirmation.

Owner observations on 2026-11-08, during the first standalone Firefox session:

- Tapping Refresh status works and increases the saved-request count. Real Goodix frames were recorded independently; basic physical touch is verified.
- **Resolved:** automatic editable-focus keyboard now uses Onboard. It appears at the bottom, physically types correctly and hides on Done; the owner confirmed all three. The keyboard's own hide key also passed a software click test.
- **Resolved:** native libinput exposes Goodix as a16-contact direct touchscreen. Owner confirmed scrolling/pinch/typing; actual browser recorded2contacts,1320pixels of scroll,3.218×zoom and ok. The pointer bridge is retained only as fallback.
- **Resolved:** keyboard now docks at the bottom with280pixel height and Firefox shrinks above it. JWM's workarea reflow correction preserves focus and restore geometry.
- Automatic portrait/landscape rotation is not integrated. A fresh read-only inventory found the stock `m_acc_misc` / `m_acc_input` accelerometer interface, with no standard IIO devices exposed. Sensor readings, orientation thresholds and matching touch-coordinate rotation still need qualification.
- YouTube reported a playback error. Experiment49 fixed the reproduced local H264+AAC failure with app-local TLS-free FFmpeg61 libraries:237frames/9.86seconds,errornull,isolatedutility/Seccomp2. The owner separately heard the quiet direct-ALSA tone. Browser audibility and actual YouTube replay remain unverified; device control was lost before their trials could run.

The owner initially deferred these until the persistent filesystem/repeat-boot foundation was complete. That foundation, automatic keyboard, native gestures and direct speaker output are now physically qualified. Rotation, browser audio and YouTube remain usability limitations.

The owner also asked whether an existing mobile distribution could provide this layer. See [tablet interface assessment](TABLET-INTERFACE.md). Preserve the working stock-kernel Alpine/WMT integration while assessing existing mobile components.

Context: the 768 MiB RAM root filled during browser testing; a later XWD capture failed with ENOSPC. The visible Firefox session passed JavaScript/fetch/canvas/localStorage/IndexedDB checks. Do not attribute the owner's playback error to storage without a repeat on the card-backed system.
