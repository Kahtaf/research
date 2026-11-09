**Paused source archive:** Current qualified features and hazards are in ../../STATE-AND-RESUME.md and ../../MEMORY.md. The installation examples below include historical RAM-stage instructions; do not install this directory wholesale or run it as a batch. Public archive files have0644 modes; review the intended installed executable modes before any future deployment.

Current physical status (2026-11-08): native Goodix/libinput scrolling, pinch zoom and bottom Onboard typing/hiding passed owner checks and a subsequent ordinary boot. The pointer bridge remains fallback only. Rotation and media are open. See ../../reports/native-goodix-libinput.md and automatic-keyboard.md.

# Goodix desktop on the ASUS stock kernel

Use with `sources/z380m-alpine` pinned to `7218a276f252a59874ab860683c061fa2b856519`.
The original bounded RAM recipe is in `../../reports/goodix-desktop-plan.md`.
This overlay also supports the independent Alpine system: it does not flash
partitions or enable a boot service itself.

`asus-goodix-desktop 20` runs the existing timed trial. Argument `0` keeps the
desktop and browser running until Xorg exits or the launcher is stopped. Arguments
5..120 retain timed mode. Persistent mode opens the browser when
`ASUS_DASHBOARD_URL` is set, leaves Terminal in Apps, and does not put a terminal
over the browser. No browser timeout is used in either mode.

Goodix is discovered by its live kernel name and verified through axis ioctls.
The patched bridge refuses missing ranges instead of assuming ELAN calibration.
Xorg requires the cookie in `/run/asus-goodix/Xauthority` and does not listen on
TCP. Cleanup checks that each recorded PID is still a child of this launcher
before signaling it. JWM maximizes normal windows when they map, preserving the
48-pixel tray; the optional xdotool check records only windows actually found for
the launched browser PID.

## Install into the Alpine root

Copy `bin/*` to `/usr/local/bin/`, `etc/X11/asus-goodix.conf` to `/etc/X11/`,
`etc/jwm/asus-goodix.xml` to `/etc/jwm/`, and
`etc/asus-goodix/firefox-user.js` to `/etc/asus-goodix/`. Install the patched bridge
from `build-touchbridge.sh` as `/usr/local/bin/z380m-touchbridge` if it is not already
installed. Preserve executable modes. The required Xorg, fbdev, evdev, xauth,
xsetroot, xset, JWM, xterm and Python packages must already be present.

`ASUS_BROWSER=netsurf` is the backward-compatible default. Set
`ASUS_BROWSER=firefox-esr` for the installed Firefox ESR. The generated Apps menu
includes Browser only when the selected browser executable exists. Keyboard
appears only when an executable supported by the keyboard wrapper exists. No
keyboard is installed or started by this overlay. Keyboard opens the available
program; it does not perform global process-name kills.

Firefox uses `/root/.mozilla/asus-appliance` by default. Its `user.js` selects
Firefox touch density, a 1.25 UI scale, no disk cache, and suppressed first-run,
welcome and default-browser prompts. Sandbox settings are unchanged. The profile
is ordinary Linux filesystem state; it remains in RAM on the current RAM root
and will persist when that root is replaced by the planned ext4 SD root. It does
not use a VFAT bind mount. `ASUS_FIREFOX_PROFILE` can choose a different Linux
filesystem directory if needed.

The launcher ensures that `/dev/shm` has a tmpfs mount with mode1777, mounting a
192MiB instance only when that exact mount point is absent. An unexpected existing
mount causes an error rather than being stacked or replaced.
`XDG_RUNTIME_DIR=/run/user/0` is created with mode0700.

## Minimal launch from SSH

Run on the independently booted Alpine tablet after installing the files:

```sh
mkdir -p /run/asus-goodix
nohup env ASUS_BROWSER=firefox-esr \
  ASUS_DASHBOARD_URL=http://127.0.0.1:8080 \
  /usr/local/bin/asus-goodix-desktop 0 \
  </dev/null >/run/asus-goodix/desktop.log 2>&1 &
```

Use the intended local dashboard URL if its service listens elsewhere. This only
starts the session for the current boot; parent-owned service integration handles
autostart. Xorg, bridge, JWM and browser logs are under `/run/asus-goodix/`. To run
X diagnostics in another SSH shell, export `DISPLAY=:0` and
`XAUTHORITY=/run/asus-goodix/Xauthority`.

## Evidence limits

Parent reports independent Alpine PID1, native Wi-Fi and LAN SSH passed. Firefox
ESR140.12 rendered an HTTPS screenshot headlessly with default sandbox settings;
NetSurf3.11 rendered in the earlier warm chroot. Those results do not qualify
Firefox under Xorg, physical taps/drags, colour correctness, UI scale or browser
persistence. The parent will test the visible desktop and capture its result.
This subtask performed no tablet or network operations.

Local checks: shell syntax, Python compilation, XML parsing and menu generation
with available/absent executable fixtures pass. The earlier bridge change was
host-compiled and checked to reject an unavailable axis ioctl. No display or
browser execution is claimed by these host checks.

All overlay code is GPL-3.0-only. Upstream copyright is retained in derivative
files. `LICENSE` is the full upstream GPLv3 text. The bridge build emits modified
source beside its binary and leaves the pinned donor checkout unchanged.
