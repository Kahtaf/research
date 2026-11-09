# Stock-kernel fbdev rotation — Opus 5.5 read-only consultation, 2026-11-08

Scope: source reading only. The tablet was not operated, no live script was edited, no sensor or calibration node was read, and nothing was delegated. Public sources were cloned read-only into `sources/rotation-spike/`, which is 32 MiB and contains nested `.git` directories. `sources/` is **not** git-ignored, so ignore or delete that folder before committing.

## Answer

**fbdev cannot rotate dynamically.** It can rotate the whole screen statically when the X server starts, through its existing `Option "Rotate"`. The smallest credible reversible route uses only components already installed. To switch between portrait and landscape, restart the existing Xorg/JWM/Onboard/Firefox session with a different fbdev `Rotate` value and a matching xf86-input-libinput `CalibrationMatrix`. It needs no new package, kernel change, nested server or compositor. An orientation change costs one desktop restart (Firefox reopens its saved session). It does not give live `xrandr` rotation.

## Source evidence

xf86-video-fbdev 0.5.0, tag `xf86-video-fbdev-0.5.0`, commit `82aa13d01340236ebb516ea45a9bd78e4fe52b79` ([src/fbdev.c](https://gitlab.freedesktop.org/xorg/driver/xf86-video-fbdev/-/blob/xf86-video-fbdev-0.5.0/src/fbdev.c), [man/fbdev.man](https://gitlab.freedesktop.org/xorg/driver/xf86-video-fbdev/-/blob/xf86-video-fbdev-0.5.0/man/fbdev.man)):

- `fbdev.c:556-587`: `Rotate` accepts `CW`, `CCW` or `UD`. It is parsed only in PreInit, it forces `shadowFB = TRUE`, and it is ignored when `shadow24` is set (a 24 bpp framebuffer). This tablet runs 32 bpp, so `shadow24` is false and rotation is allowed.
- `fbdev.c:546-547`: ShadowFB is **on by default**. The current unrotated desktop already draws through the shadow → `/dev/fb0` copy path (`shadowUpdatePacked`). Rotation only swaps that copy routine for `shadowUpdateRotatePacked` (`fbdev.c:718-725`). The proven mtkfb write path is unchanged.
- `fbdev.c:829-833`: for CW or CCW, `virtualX` and `virtualY` are swapped at ScreenInit. The X screen becomes 1280×800.
- `fbdev.c:1265-1277`: `FBDevDriverFunc` handles only `GET_REQUIRED_HW_INTERFACES`. It does not handle `RR_GET_INFO` or `RR_SET_CONFIG`.
- xserver 21.1.25, commit `edc1b378f804ef5bf286318057e0b935f91f22b7`, [`hw/xfree86/common/xf86RandR.c:74,131-138`](https://gitlab.freedesktop.org/xorg/xserver/-/blob/xorg-server-21.1.25/hw/xfree86/common/xf86RandR.c): the RandR 1.1 compatibility path starts with `RR_Rotate_0` and widens it only if the driver answers `RR_GET_INFO`. **This exactly explains the measured mask1/current1.** Dynamic rotation would need a new patch to the fbdev driver. That is out of the existing-component scope and is not recommended now.
- `fbdev.c:948-956`: with ABI ≥ 24 (Xorg 21.1) the driver no longer calls `xf86DisableRandR`. A rotated session should therefore still report one 1280×800 size with rotation mask 1.

Touch: xf86-input-libinput 1.5.0, commit `c712930ef4b544a5036fe2f55fd2ade9efb8ea78` ([man/libinput.man:94-98](https://gitlab.freedesktop.org/xorg/driver/xf86-input-libinput/-/blob/xf86-input-libinput-1.5.0/man/libinput.man)), supports `Option "CalibrationMatrix"` and the runtime property `libinput Calibration Matrix`. libinput applies the matrix to touch coordinates before XI2 touch events are sent, so the direct 16-contact class is kept. The fbdev wrapper `FBDevPointerMoved` (`fbdev.c:1079-1112`) only handles viewport/cursor panning. It does **not** remap absolute touch input, so a matrix is needed.

The matrices below are derived from fbdev's own coordinate map: `CW` = shadow `RR_Rotate_270` = xrandr "right". This assumes the panel axes already match the unrotated framebuffer, which the current untransformed touch proves.

| fbdev `Rotate` | X screen | `CalibrationMatrix` |
|---|---|---|
| (none) | 800×1280 | `1 0 0 0 1 0 0 0 1` |
| `CW` | 1280×800 | `0 1 0 -1 0 1 0 0 1` |
| `CCW` | 1280×800 | `0 -1 1 1 0 0 0 0 1` |
| `UD` | 800×1280 | `-1 0 1 0 -1 1 0 0 1` |

Onboard: `overlay/goodix/bin/asus-goodix-osk:24-25` already sets both `org.onboard.window.portrait` and `org.onboard.window.landscape` dock-height to 280. Onboard picks the set that matches the screen's aspect ratio, so it should dock full-width at the bottom of 1280×800 with no code change. 280 of 800 lines is 35% of the screen; reducing the landscape height is an optional later tweak. JWM's workarea patch has no fixed geometry. The desktop helper's only fixed geometry is an xterm size.

## Rejected leads

- **Nested Xephyr (software-rendered):** its RandR does support 90/270 rotation (`hw/kdrive/ephyr/ephyr.c:403,599,615`). However, ephyr's input is a plain `KdPointerDriver` (`ephyr.c:1309`), and `hw/kdrive/ephyr/*.c` contains no touch or XI2 code. Firefox inside it would lose the qualified XI2 direct-touch class, which carries scrolling and pinch. Using it would trade a working capability for rotation. Rejected.
- **Wayland or a framebuffer compositor, or another distribution:** excluded by scope. There is no DRM device.
- **Kernel `fb_var_screeninfo.rotate` / fbcon rotation:** this would need unverified support in the vendor mtkfb driver, and fbcon rotation affects only the console. Not relied on.
- **CSS rotation:** does not count as whole-screen rotation.

## ONE bounded next experiment (owner present, timed revert)

Set up a manually selected landscape session (`CW`), using the same guarded pattern as the native-touch trial. Do not automate the accelerometer yet.

1. Write a private candidate X config: a copy of the generated `/run/asus-goodix/native-xorg.conf` that adds only `Option "Rotate" "CW"` to the `fb0` Device and `Option "CalibrationMatrix" "0 1 0 -1 0 1 0 0 1"` to `touch0`. Use a new marker, e.g. `/etc/asus-goodix/rotation=cw-v1`. Leave the existing helpers and `/etc/X11` files as rollback; choose the variant only through the marker.
2. Restart the desktop session once with the candidate. Start a revert watchdog (for example 6 minutes, timed from browser readiness) that removes the marker and restarts the normal session unless the owner accepts.
3. Afterwards, return to the unrotated session and confirm native input and Onboard still pass.

**Positive gate (all required):**
- The Xorg log contains `rotating screen clockwise` and `using shadow framebuffer`.
- The root window or `xrandr` reports 1280×800.
- The owner sees correctly oriented, untorn landscape output on the physical panel.
- Taps land under the finger at all four corners and the centre.
- One-finger scroll and pinch work in Firefox, and XI2 still lists the direct-touch class.
- Onboard docks full-width at the bottom on focus, types and hides.
- Firefox resizes to the 1280-pixel width above the keyboard.
- Xorg CPU use while scrolling stays acceptable. Record it; the rotated shadow copy is the only new cost.
- Removing the marker restores the 800×1280 session with the same native input.

**Negative gate (stop; do not try other variants):**
- Xorg fails, or the panel is black or garbled. Read the Xorg log and leave the normal session running.
- Touch is mirrored or misplaced under the derived matrix. One property swap at runtime, `xinput set-prop touch0 "libinput Calibration Matrix" …` with the CCW matrix, is a measurement, not a new variant. If neither matches, the panel-axis assumption is wrong; record it and stop.
- Scrolling is unusably slow because of the rotated copy.

If the positive gate passes, portrait/landscape rotation works through a session restart. Automatic rotation would then need only a separate sensor gate: read `m_acc_input` from the documented stock enable/report ABI, never touch `gs_cali`/`resetcali`, and trigger the same restart. If the negative gate fires on display output, no practical path exists inside the existing-component scope. The exact blocker is fbdev's missing `RR_GET_INFO`/`RR_SET_CONFIG` together with the static PreInit `Rotate` option. The smallest next action would then be a reviewed, local-only patch to `FBDevDriverFunc` adding shadow re-rotation, which is a new driver build and needs the owner's approval.
