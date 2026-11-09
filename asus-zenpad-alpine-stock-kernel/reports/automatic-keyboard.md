# Automatic keyboard experiment — 2026-11-08

Onboard1.4.4.2-r0, AT-SPI and session D-Bus installed from stable Alpine3.24 aarch64 repositories. The Atspi GI typelib imported on the actual stock3.18.35 kernel. The transaction added23 packages, approximately38MiB, bringing the package footprint to686MiB. No mobile desktop replacement or kernel change was needed.

Latest: the normal desktop integration and owner physical check PASSED. Onboard is enabled automatically; the browser is back on the dashboard. The sections below retain how the component was qualified.

## Isolated runtime result

`scripts/osk-focus-trial.py` ran for a bounded180seconds under its own dbus-run-session, while the existing Xorg/JWM and owner's Firefox profile remained running. XDG configuration/cache and the separate trial browser profile stayed under an owned /tmp directory. It updated the private bus activation environment before setting preferences so dconf did not write the owner's main settings.

Firefox's real HTML editable focus caused Onboard to appear automatically, docked at the bottom: x0,y1032,width800,height200, with the48pixel JWM tray below. The key was selected with an XTEST mouse click on the actual rendered Onboard key, rather than injecting a keyboard character directly. The browser received `a` and kept editable focus. Moving focus to the noneditable Done button automatically hid the keyboard; refocusing the field showed it again. The trial supervisor reached its deadline and both owned children exited after TERM, without SIGKILL. The original browser/profile was not used by this test.

This proves the software input/focus path on the tablet. Physical typing through Goodix was subsequently verified by the owner: all three requested behaviors worked, and the browser recorded tablet. The keyboard's own hide key also passed a software click. The earlier owner-confirmed Goodix dashboard tap is separate evidence and does not by itself qualify keyboard typing.

## Layout defect and correction

Onboard correctly published a bottom248pixel strut and JWM correctly published workarea height1032. However, the already-maximized browser kept its original height and overlapped the keyboard. This is a window-manager behavior, not an Onboard docking or sensor problem.

Exact JWM2.4.6 source handles strut changes by publishing workarea without reflowing existing maximized clients. Calling its normal MaximizeClient action would also raise/focus the target. The source correction was compiled on the tablet under the120second bound with the same packaged features, then deployed separately as /usr/local/bin/asus-jwm. The packaged /usr/bin/jwm hash remains107bd16aaaa575750c44b2d3f6cd9606c6759acef3e7464c06e909e793dcd58b. Actual browser resizing passed: client height909 with the280pixel dock at y952, height1189 when hidden. Restore geometry stayed x48,y118,width720,height1109, and typing kept focus. No raise/focus workaround daemon was added.

Private raw outputs are experiment34 and osk-trial-* under private/live. Sanitized software proof is evidence/automatic-keyboard-trial.json. The capture scripts now support both24- and32-bit XWD pixels; the observed keyboard capture is a24-bit ZPixmap with3200byte row stride. Its decoded image was visually inspected.

## Scope

Production integration uses one session bus shared by JWM-launched Firefox and Onboard, accessibility enabled and a manual Apps → Keyboard toggle. Browser sandbox defaults remain unchanged. Automatic keyboard is one component of the tablet interface; native touch scrolling, rotation, video and sound remain separate work.


## Deployment and rollback

The SD OS has enable markers `/etc/asus-goodix/automatic-keyboard` containing `onboard-v1` and `/etc/asus-goodix/jwm-workarea` containing `jwm-2.4.6-workarea-v1`. Desktop source enters dbus-run-session and records its actual inner controller PID. Onboard uses persistent dconf settings, a280pixel bottom dock and Compact layout. The browser keeps its existing profile and sandbox defaults. The Browser menu targets its Navigator client, excluding hidden GTK helper windows.

Original live helper files and their receipt are under the protected SD folder `private/desktop-before-onboard`. The packaged JWM binary was never replaced. To disable the additions, close the owned desktop through the guarded SSH helper, rename only these two enable markers to disabled names, and restart from a fresh SSH environment; the updated desktop then uses packaged JWM and the previous manual keyboard path. Do not rewrite recovery or BCB for this UI rollback. Inspect process identity before stopping anything.

The JWM candidate is SHA256789dbb085e8485ff69b177cd8da8c4effe75028dfcdbf1cd4119a0959c910bc6. Its MIT license and patch are retained at `/usr/local/share/doc/asus-jwm`. Source and build provenance are under evidence/jwm-reflow. Temporary compiler packages were removed. The keyboard and subsequent native libinput revision later passed an ordinary kernel reboot, including cold Wi-Fi, stable SSH, dashboard and HTTPS.

The ten-minute fixture was stopped after the physical check and the owner browser returned to the dashboard. User report and actual tablet input events are in evidence/automatic-keyboard-physical.json and private/live/onboard-physical-state.json. Synthetic navigation initially hit a GTK helper/focus race, and a visibility check initially counted transitional keyboard windows; those checks were corrected before the owner check. They are not touchscreen failures.
