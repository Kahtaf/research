# Independent use: current capabilities and completion plan

The tablet is a real current Alpine userspace on its original3.18.35 kernel. It is not yet a finished consumer tablet. Its normal microSD boot, saved-network Wi-Fi, SSH, dashboard and touchscreen desktop start without the Mac. Profile, OS files and dashboard SQLite data persist. Ordinary reboot has been demonstrated; cold power-off/on and suspend/resume have not. The Mac is a management/recovery tool rather than a runtime dependency.

## Actual hardware audit — 2026-11-09

A read-only check on the pinned live Alpine boot found mtk-kpd(event1) advertising KEY_POWER116, KEY_VOLUMEUP115 and KEY_VOLUMEDOWN114. This is capability evidence, not evidence of real presses or working actions. Xorg auto-add is disabled; the explicit working device is Goodix touch. There are no JWM power/volume bindings and no tablet button controller. Do not claim short-press screen blank/wake, volume change or long-press orderly shutdown. Do not test long holds unattended.

There is no /sys/class/bluetooth, no active HCI controller, no stpbt or stpbt1 node and no bluetoothd/bluetoothctl installed. Bluetooth is not brought up or tested. Stock firmware has a vendor MediaTek WMT/BT transport, so installing BlueZ alone is not known to establish it. Any later BT experiment must preserve the working shared Wi-Fi/WMT lifecycle; never rerun the WMT loader on a warm kernel.

lcd-backlight exists in the LED class, not the standard backlight class. Existing GUI startup already has a brightness recovery path. This audit did not read driver-specific calibration/sensor controls, change brightness, blank the display, suspend, reboot or activate Bluetooth.

## Minimum everyday tablet milestone

1. Build one small on-device control surface: Home/Browser, Terminal, Keyboard, Wi-Fi status/network selection, brightness, volume/mute, Restart and Shut down. Destructive actions need confirmation on the tablet, not remote surprise actions. Keep the existing lightweight JWM and working Onboard/native touch.
2. Wire the actual keypad to a safe screen blank/unblank path and software volume. Qualify physical key delivery first. Keep full suspend separate until the wake path and network recovery are established. Do not infer orderly shutdown from PMIC long-hold behavior.
3. Finish ordinary sound: owner can use Apps > Speaker check when convenient. Its browser route software gates passed, but normal always-available speaker management is not enabled and hearing is unconfirmed. Promote the reviewed amplifier lifecycle only after that gate.
4. Make desktop and small service failures recover automatically, and provide an on-device way to reopen them. Validate Wi-Fi loss/reconnection and service restart using one bounded realistic workload.
5. When physical recovery is available, qualify one clean full shutdown and power-on without the Mac, verify Wi-Fi/SSH/desktop/data, then assess screen-off battery use. Do not promise suspend, long runtime or unattended cold recovery before this.
6. Publish one concise owner guide and preserve an offline, private, consistent rollback/backup procedure. An internal installation or dual-boot menu is not required to use the existing microSD system independently.

Bluetooth and automatic rotation are follow-on conveniences, not prerequisites for the minimum milestone. Rotation remains parked on the unmatched sensor-hub lifecycle.

## Useful work

Already demonstrated: Firefox web content, native touchscreen browsing, a local Python HTTP dashboard, SQLite persistence and key-only SSH management. Apps > Terminal offers local shell access; Apps > Keyboard can explicitly show the keyboard for terminal interaction. These foundations support small shell/Python tools and local web interfaces; each newly installed service still needs its actual stock-kernel workload checked.

Best first product: a simple home/desk control terminal. Show a few useful web dashboards or locally stored reference pages, connect to the Mac for heavy jobs, and optionally keep one small local Python/SQLite service. Home Assistant is an example of a browser-hosted dashboard on another server, not a service we have connected here: https://www.home-assistant.io/dashboards/ . A future low-rate MQTT broker/logger is plausible; Mosquitto is designed for low-power devices, but is not installed or qualified here: https://mosquitto.org/ .

Other candidates: distraction-free writing, an offline reading/reference shelf with an appropriate viewer, timers and checklists, a household inventory, low-rate LAN status logging and a touch front end to Mac-hosted automation. These are proposed uses, not claims that all apps are installed. Prefer one concrete everyday role before adding several services.

The current graphics path is software framebuffer, Bluetooth is unavailable, speaker integration is incomplete and battery/suspend behavior is unqualified. Avoid positioning this as a modern Docker host, heavy development workstation, high-resolution media appliance or public internet server. Keep heavy computation on the Mac and access local services over the trusted LAN/SSH.

Evidence: evidence/independent-use-hardware-audit.json; ignored raw private/live/standalone-hardware-status.txt. No new hardware writes or active trials were performed for this assessment.
