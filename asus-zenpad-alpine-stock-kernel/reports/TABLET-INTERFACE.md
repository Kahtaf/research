# Tablet interface assessment — 2026-11-08

**2026-11-09 decision update:** The owner prioritizes polished, functional tablet use. Current recommendation is one reversible native Xfce-on-Alpine trial, with Android+Termux/X11 as a distinct hybrid option for retaining Android hardware integration. Sxmo is no longer the first UI candidate for this preference. No ready complete Z380M mobile-Linux image was established. See [fresh research and primary sources](interface-recommendation-2026-11-09.md). Historical observations below include superseded state; MEMORY.md remains authoritative.

The owner wants automatic keyboard presentation on input focus, a bottom-docked keyboard, touch scrolling, portrait/landscape rotation and practical media playback. Basic physical Goodix tapping is confirmed. These additional behaviors are not qualified by a working Xorg desktop.

## Actual hardware and current session

The running stock 3.18.35 kernel exposes `m_acc_misc` controls and an `m_acc_input` evdev device. A read-only inventory found no IIO sensor devices or DRM display devices. This establishes an available legacy sensor interface, not functioning automatic rotation. Do not carry the older 4.9 audit's missing-driver conclusions onto this stock kernel.

The current display path is Xorg fbdev on `/dev/fb0`, corrected JWM, Onboard and native Goodix/libinput input. The donor bridge is retained only as pointer fallback. The current svkbd launcher is manual; its observed top placement is not a sensor or orientation failure. The browser launcher exports `NO_AT_BRIDGE=1` and a memory settings backend; an AT-SPI keyboard needs a shared session bus and accessibility enablement. ESR140 can override `NO_AT_BRIDGE` when its accessibility bridge initializes, so that variable alone is not evidence that Firefox cannot expose a tree.

Fresh direct-input experiment31–32: live Goodix capabilities have MT_SLOT/MT_X/MT_Y/MT_TRACKING_ID and INPUT_PROP_DIRECT, but no legacy ABS_X/ABS_Y/BTN_TOUCH/BTN_TOOL_FINGER. A private dummy Xorg screen with the installed evdev driver exposed it as a relative device without XITouchClass. The original desktop was left running. Direct evdev substitution therefore does not preserve usable touch on this setup; native libinput was subsequently tested and passed direct16-contact input. It already includes Android MT compatibility, so a new bridge was unnecessary. Physical scrolling, zoom and keyboard passed and survived reboot.

Firefox's menu launch could create a second process and a profile-in-use dialog. The persistent browser wrapper now validates the live profile owner and raises its existing X window. Actual execution retained the same owner and brought Firefox forward; no profile/history was deleted. This small repair does not qualify automatic keyboard or gestures.

## Existing mobile software

[postmarketOS](https://postmarketos.org/) is based on Alpine and integrates mobile interfaces. Reusing its components is compatible with retaining the proven Alpine core, but a different root filesystem does not by itself adapt this ASUS vendor display, sensor or audio interfaces. No ready-made supported Z380M image was established in this assessment.

[Sxmo](https://sxmo.org/) explicitly supports legacy Xorg as well as Wayland. Its [manual](https://sxmo.org/docs/user/sxmo.7.html) documents lisgd gestures, keyboard controls and rotation hooks. This is the closest architectural fit to the current fbdev/Xorg path and a reasonable bounded next trial. Its [getting-started guide](https://sxmo.org/docs/gettingstarted/) explicitly makes keyboard opening a manual gesture/button action, rather than automatic input-focus behavior. Do not present it as a complete match for the owner's keyboard requirement.

Onboard1.4.4.2 is available in Alpine3.24 stable aarch64. It and AT-SPI/D-Bus dependencies installed successfully on the tablet (23 additional packages, total package footprint686MiB). The actual Atspi typelib import passed. Onboard offers automatic focus-driven showing and bottom docking without changing JWM. The isolated private-bus/temporary-profile experiment passed, followed by normal desktop integration. The owner then physically typed tablet and confirmed bottom appearance, correct typing and hiding. See automatic-keyboard.md.

[Phosh](https://guidog.pages.gitlab.gnome.org/phosh/gettingstarted.html) is an integrated mobile shell, normally using the phoc Wayland compositor and sensor services. It is a candidate for the desired interaction model. Direct compatibility with this framebuffer-only running kernel remains unproved. The [old postmarketOS framebuffer integration issue](https://gitlab.com/postmarketOS/pmaports/-/issues/948) describes a separate wlroots framebuffer backend proof of concept; that archived proposal is not current shipping support or justification to install an arbitrary historical compositor.

[Plasma Mobile's current porting documentation](https://develop.kde.org/docs/plasma-mobile/porting/) specifies mainline Linux and says previous Halium support was dropped. It is a poor immediate match for the fixed stock-kernel scope.

## Next scoped work

Repeat-boot and stock-return qualification of the microSD OS are complete. Automatic keyboard now works through Onboard on the existing desktop; no new mobile shell is needed for that requirement. Retain stable Wi-Fi, SSH identity and the owner's browser profile. Establish native touchscreen multitouch delivery before claiming gestures. Treat sensor-driven display rotation and touch-coordinate transformation as one acceptance check. Choose an automatic keyboard path explicitly; Sxmo's default manual behavior is insufficient. Diagnose video playback and speaker routing independently.

Do not replace the working system, resume the 4.9 port or add several competing desktops merely to evaluate these options.


Latest native-input result: experiments39–44 installed only4MiB of input dependencies, proved native XI2 direct16-contact class, corrected Xorg Device configuration to canonical event path, then physically qualified scrolling/pinch/typing. Runtime udev metadata is recreated by the guarded helper without a daemon. The first bounded trial automatically returned to old input before user interaction; the second started timing at page readiness and was accepted after owner confirmation. Current ordinary boot autostarts native input and keyboard. Rotation is separately limited by fbdev RandR mask1; media is still open.
