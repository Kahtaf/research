# Goodix desktop adaptation

Status: implementation prepared and host-checked; no tablet operation by this subtask. Parent supplied fresh physical evidence: `goodix-touchscreen`, currently event11, type B, MT X 0..800, Y 0..1280, slots 0..15, direct input. Framebuffer is 800×1280 with 32 bpp and stride 3200, virtual height 3840. This is not physical click/drag qualification.

The pinned donor is `kaantcp/z380m-alpine` commit `7218a276f252a59874ab860683c061fa2b856519`. Its touch bridge already accepts `-i DEV` and reads axis ranges using EVIOCGABS. Its generic desktop discovery would find Goodix, but it silently falls back to the donor ELAN ranges if an ioctl fails. The overlay removes that fallback; no new touch state machine is needed.

## Files

- `overlay/goodix/touchbridge-no-fallback.patch`: require successful, nondegenerate kernel axis ranges for both `run` and read-only `probe`.
- `overlay/goodix/build-touchbridge.sh`: copy upstream source into ignored artifacts, apply the small patch, build the same freestanding aarch64 bridge. Needs clang and lld; no aarch64 libc/sysroot. Upstream is unchanged.
- `overlay/goodix/bin/goodix-preflight.py`: select exactly one panel by the observed Goodix name, verify real char node and live X/Y/slot ioctls. Reject slots beyond the donor's 16-slot capacity; print actual ranges instead of assumed calibration.
- `overlay/goodix/etc/X11/asus-goodix.conf`: upstream GPL configuration with only the explicit bridge symlink changed. Uses fbdev + evdev, no GLX or automatic device discovery.
- `overlay/goodix/bin/asus-goodix-desktop`: 20-second default Xorg/JWM/terminal trial, authenticated local X socket and no TCP listener, bridge and X/session cleanup. Duration accepts 5..120 seconds; the parent should use 20 under its existing 60-second root limit.
- `overlay/goodix/etc/jwm/asus-goodix.xml`: large menu and tray targets and a terminal entry. Add a browser entry only after its executable and workload have been verified.

GPL-3.0-only notices and upstream authorship are preserved. The overlay includes the unmodified upstream license. Modified source is produced beside the binary for review.

## Exact bounded RAM recipe

This is a parent-operated recipe after reviewing current Android state. It does not write BOOT, SYSTEM, recovery, GPT, factory data or the physical SD card. The existing root helper has only a 60-second root window and restores Enforcing. Keep package installation and binary transfer outside the display-stop window.

1. Build `sh overlay/goodix/build-touchbridge.sh`. Copy its resulting `z380m-touchbridge.arm64` to the **RAM root** `/usr/local/bin/z380m-touchbridge`, the overlay `bin/*` to `/usr/local/bin/`, Xorg config to `/etc/X11/`, and JWM XML to `/etc/jwm/`. Do not run donor's flash installer or service/autostart installer.
2. In a separate on-demand root session, with `R=/data/local/tmp/asus-alpine-ram`, install only `xorg-server xf86-video-fbdev xf86-input-evdev xauth xsetroot xset xterm jwm font-dejavu`. The RAM root already has Python. Install a browser only after checking its size and dependencies; it is not necessary for the first display trial.
3. Mount a separate sysfs instance on `$R/sys` if none exists. Under the RAM root's private `/dev`, create fb0 and uinput from `/sys/class/graphics/fb0/dev` and `/sys/class/misc/uinput/dev`; create the Goodix event node by discovering the matching `/sys/class/input/event*/device/name` and its `dev` number. Do not bind Android's whole `/dev`. `/proc` and devpts were prepared by the parent. Run `chroot "$R" /usr/local/bin/goodix-preflight.py`, then `chroot "$R" /usr/local/bin/z380m-touchbridge probe -i /dev/input/<discovered-event> -t 1`. Probe must report the actual ranges. A no-finger result is not a touch failure.
4. Inspect `getprop init.svc.surfaceflinger`, `init.svc.zygote`, `init.svc.zygote_secondary` and capture their initial states. Abort if the assumed stock services differ. Then run the following through the existing root helper; the subshell restores only the services it stopped:

```sh
R=/data/local/tmp/asus-alpine-ram
[ "$(stat -f -c %T "$R")" = tmpfs ]
[ "$(getprop init.svc.surfaceflinger)" = running ]
[ "$(getprop init.svc.zygote)" = running ]
secondary=$(getprop init.svc.zygote_secondary)
restore_display() {
  set +e
  start surfaceflinger
  start zygote
  [ "$secondary" = running ] && start zygote_secondary
}
trap restore_display EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
[ "$secondary" != running ] || stop zygote_secondary
stop zygote
stop surfaceflinger
sleep 1
timeout 35 chroot "$R" /usr/bin/env -i HOME=/root \
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  /usr/local/bin/asus-goodix-desktop 20
```

5. Read `$R/run/asus-goodix/{Xorg.log,bridge.log,jwm.log,xterm.log}` in the next root session, verify Android's saved service states returned, boot-complete recovers and SELinux is Enforcing. The trial intentionally expires. Do not mark it persistent or cold-boot-qualified.

On failure, inspect the single failing layer before another trial. If Xorg reports a format/VT problem, use the donor's documented diagnostics; no colour preload or axis inversion is enabled without physical evidence. Do not perform generic process-name kills against Android or donor services.

## Qualification limits

Successful Xorg/JWM launch and a nonempty framebuffer establish rendering on the real kernel, not that the owner can tap correctly. Physical taps/drags must produce bridge frames and move/click the X pointer; verify corners and one drag without excessive testing. Synthetic events are only an input-pipeline check. Native Goodix multitouch remains represented as one pointer by design. No on-screen keyboard is included yet.

The bridge needs `/dev/uinput`; absence is a concrete next blocker, not a reason to assume Xorg evdev handles this panel directly. Read-only device discovery does not prove pixel orientation or colour correctness. Android SurfaceFlinger may reset display format on restoration; that also needs observation. No claim here establishes browser support on kernel3.18, independent Linux PID1 boot, standalone WMT cold start or service persistence.

Host validation: shell syntax passed; patched C compiled with `clang -DTESTBUILD -Wall -Wextra -O2`; version output preserved upstream credit. `probe -i /dev/null -t 1` exits1 with an axis-unavailable error instead of producing ELAN ranges. This intentionally tests the changed failure behavior only. The generated aarch64 binary has not been built or executed by this subtask.
