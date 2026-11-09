# Native Goodix multitouch — physically qualified

Alpine stable libinput1.31.3-r0, xf86-input-libinput1.5.0-r0 and eudev3.2.14-r6 support the stock panel's MT-only Android protocol. Libinput's Android compatibility path supplies missing legacy X/Y internally; MT contact transitions use tracking IDs rather than requiring BTN_TOUCH. No kernel change or custom MT bridge was needed.

The actual device has MT_SLOT, positionX/Y, trackingID and INPUT_PROP_DIRECT, but no legacy X/Y or touch button. Raw evdev failed to expose touch; a private dummy Xorg/libinput context with truthful runtime udev tags exposed XITouchClass, direct mode, maximum16contacts. Metadata was restored after the headless probe.

The permanent helper validates unique panel identity, char-device numbers, MT axes and eudev input_id classification. It prepares only ID_INPUT=1 and ID_INPUT_TOUCHSCREEN=1 in the derived root-owned runtime metadata file, without running udevd or triggering hardware discovery. Existing conflicting metadata is refused. Desktop selects native mode only through its explicit marker; the tested pointer bridge remains fallback.

The Xorg driver requires the canonical Device path: its open_restricted callback literally compares it against udev's devnode. The initial alias configuration failed and was corrected to a runtime template filled from validated preflight. Browser starts with MOZ_USE_XINPUT2=1. Firefox ESR140 GTK's base-widget maxTouchPoints API returns0; this was an invalid qualification assertion, removed without spoofing preferences. Actual touch events are the gate.

A six-minute physical trial rolled back before interaction. A fresh trial started its countdown only after browser readiness. Owner confirmed scrolling, pinch and typing. Browser events corroborated2contacts, scrollY1320, scale3.2183437, pointerType touch and ok. ACCEPTED stopped the watchdog. No synthetic touch or wheel events were injected to obtain those observations.

The next ordinary kernel reboot passed native16-contact touch, recreated metadata, automatic keyboard, FirefoxXI2, cold Wi-Fi, stable-key LAN SSH, persistent dashboard count41 and HTTPS. The transient fixture/watchdog did not restart. All UI/input changes live in the SD OS; no recovery or BCB writes were made for this work. Original normal BOOT, bootloader, GPT and factory state remain preserved.

Evidence: evidence/native-touch-physical.json; private experiment40–44 outputs and native-touch-physical-state.json. Source: overlay/goodix/bin/goodix-native-input.py, the two Xorg configs and desktop/browser launchers. Source helpers/canonical-path contract also checked after promotion. Native-input rollback is documented in OPERATING.md.
