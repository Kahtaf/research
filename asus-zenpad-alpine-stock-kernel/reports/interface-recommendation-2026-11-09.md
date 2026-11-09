# A usable, attractive Linux tablet: recommendation

The owner prioritizes an attractive, functional, light tablet over proof that a modern userspace boots. The current JWM desktop does not meet that product goal. Retaining its working hardware integration is useful, but JWM is not the recommended final interface.

## Verdict

For native Linux on this exact ASUS Z380M/P00A_2, the best-supported next experiment is **Alpine plus Xfce**, retaining native Goodix input, Onboard, the safe audio bridge, stock WMT and the microSD root. This is a compatibility-based recommendation, not an actual tablet performance result. Xfce is a complete modular desktop with application launcher, file manager and settings. Its compositor can be disabled, fitting the existing software fbdev/X11 path. Use a cohesive theme, large touch targets and a simple panel. It remains a desktop adapted for touch, not an Android-equivalent mobile shell.

For the most functional tablet experience today, the stronger practical candidate is **stock Android as the tablet interface, with Termux/Linux tools alongside it**. Current official Termux and Termux:X11 documentation supports Android7; X11 explicitly documents an Xfce session. This preserves Android's existing hardware integration instead of reproducing every HAL feature. It is a hybrid, not a replacement native Linux distribution. It has not been installed or benchmarked on this tablet. Android7 remains an old OS; this is not a claim of modern Android security or universal current-app compatibility. Termux packages are Android/Bionic builds, not the existing Alpine filesystem. Reusing Alpine via a separate rooted chroot would be another implementation task; never mount the same ext4 OS image twice or discard the native install/profile.

No ready-made Linux image was found that establishes complete Z380M hardware support and Android-level everyday usability. A generic ARM64 download does not supply a tablet-specific boot/display/power/radio port.

## Alternatives assessed

- **LXQt:** attractive, modular, lightweight X11 desktop. The official project supports arbitrary X11 window managers. A valid second candidate, but neither memory advantage nor its Onboard/Qt accessibility behavior has been measured here. Choose Xfce first to stay close to the already-working GTK/accessibility stack. Do not trial several desktops together.
- **Phosh / Mobian / postmarketOS:** a more appropriate mobile-first UX, with app launcher, settings and screen keyboard. Phosh uses the phoc Wayland compositor. Mainline support is its main target; Android-kernel use exists through a separate Droidian/Halium stack. The current ASUS has a qualified fbdev/Xorg path, no working DRM/GPU path, and no established Phosh device image. This does not prove Phosh can never run; it makes a full switch a graphics/device-port project, not a low-risk distro replacement.
- **Plasma Mobile:** visually attractive mobile shell, but current KDE porting documentation requires mainline Linux and explicitly dropped Halium support. Not a fit for the fixed stock3.18 kernel scope.
- **Ubuntu Touch / Lomiri:** integrated touch UX, but Z380M is absent from the current official device list. Its documentation says unlisted devices need a port. No ready installer for this ASUS was established.
- **Droidian:** deliberately targets Android hardware, but its official porting guide requires Android9 or a working Android9 port. This tablet is stockAndroid7; no Android9 base was established. Do not resume the parked Android/kernel port work to chase it.
- **Sxmo:** technically plausible through its legacy Xorg path and hardware hooks. It is deliberately menu/gesture driven, has a learning curve, and its default keyboard is explicitly manual. It is a poor first recommendation for this owner's request for polished, familiar tablet behavior.
- **Replacing Alpine with generic Debian/Ubuntu/Arch userspace:** does not resolve the same missing hardware lifecycle or create a mobile shell. A package-manager change alone does not establish kernel/init/display compatibility. No generic PC image should be flashed.

## One bounded next trial

Research is complete for this decision; no OS switch or tablet configuration change was performed. If proceeding with native Linux, prepare one separately selectable Xfce session on the SD system, preserve JWM fallback and profile, and keep unqualified power managers/automatic suspend/radio managers from changing the known hardware paths. Disable compositing and use the current safe PulseAudio route. Check actual touch typing, keyboard work-area resizing, settings/file management, browser startup/responsiveness and memory on the tablet. Measure before claiming faster or smoother. An attractive shell alone cannot qualify Bluetooth, sensor rotation, ordinary speaker lifecycle or cold power/suspend.

The full everyday-usability acceptance remains the one in INDEPENDENT-USE.md: on-device Wi-Fi/brightness/volume/power controls, working buttons, normal sound, service recovery, then physically available shutdown/power-on. Do not turn this into a custom mobile-shell rewrite or several speculative rootfs variants.

## Primary sources checked 2026-11-09

- Xfce components: https://www.xfce.org/about/
- Xfce compositor-off startup: https://docs.xfce.org/xfce/xfwm4/introduction
- Actual project appearance: https://www.xfce.org/about/screenshots/
- LXQt X11/modularity: https://lxqt-project.org/about/
- LXQt themes/screenshots: https://lxqt-project.org/screenshots/
- Both Xfce4.20.2 and LXQt2.4.0 session packages are present in Alpine3.24 community aarch64: https://dl-cdn.alpinelinux.org/alpine/v3.24/community/aarch64/ . Package availability does not prove old-kernel runtime compatibility.
- Phosh components: https://phosh.mobi/about/
- Phosh device/distribution/Android-Halium caveats: https://phosh.mobi/faq/
- Plasma hardware requirements: https://develop.kde.org/docs/plasma-mobile/porting/
- Ubuntu Touch supported devices and port requirement: https://devices.ubuntu-touch.io/
- Droidian requirements: https://github.com/droidian/porting-guide
- Sxmo Xorg support: https://sxmo.org/
- Sxmo default keyboard/menu behavior: https://sxmo.org/docs/gettingstarted/
- Termux Android>=7 support: https://github.com/termux/termux-app#installation
- Termux:X11 Android7 and Xfce instructions: https://github.com/termux/termux-x11#setup-instructions

The postmarketOS device wiki redirected to wiki.nura.eco and denied automated access. Exact-model searches did not establish a ready Z380M image; this is an unsuccessful search, not proof that no unofficial experiment exists. No Reddit posts were used as technical evidence. Official project screenshots saved under ignored artifacts/interface-choice/ are illustrative upstream desktops, not screenshots of this ASUS or a tested installation.
