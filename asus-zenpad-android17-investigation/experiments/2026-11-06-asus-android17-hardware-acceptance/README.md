# ASUS Android 17 hardware acceptance

Question: after the port boots, what real evidence establishes a useful tablet
with working display/touch, Wi-Fi, Bluetooth, battery/charging and Google Play?

Status: bounded read-only collection tool prepared. No Android17 hardware boot
or acceptance pass is claimed. The target is the exact ASUS DEVICE_SERIAL_REDACTED.

Run scripts/collect_hardware.py --plan to inspect commands without device
access. With the ASUS running the new OS, run without --plan. The collector
requires SDK37 before recording an Android17 session and never reboots, roots,
formats, changes radios, pairs devices or alters settings. It preserves each
command's return code and timeout and limits outputs. Logs remain private local
files; do not upload them to the public source tree or cloud builder.

Outputs: artifacts/private/<UTC-time>/report.json and per-command text evidence.
A report is observations, not an automatic hardware pass. Continue through the
functional steps below after reviewing the collected evidence.

## Functional completion requirements

- Actual SDK37 framework reaches boot completion; repeat after a cold boot.
- Display shows correct orientation/colors and resumes after screen off/on.
  Touch reaches a 3x3 grid including all edges, supports drag and intended
  multitouch without stuck contacts. Input inventory alone proves none of this.
- Wi-Fi joins the user's chosen network, routes real traffic and survives
  suspend/resume. A reported enabled radio or IP address alone is insufficient.
- Bluetooth discovers and pairs with a chosen known accessory, transfers the
  intended audio/input/data, reconnects and survives suspend/resume. Existing
  stock discovery evidence is only a baseline.
- Battery voltage/temperature/level come from actual gauge/charger interfaces.
  Charge enable remains inhibited until the real driver/gauge path is ready.
  After that gate is cleared, observe USB attach/detach, real positive charging
  behavior and stable temperature; do not infer charge from the cable icon.
- Play services and Store remain installed/enabled, matching Google components
  activate, account setup works, and a Store app installs/updates after reboot.
  Package presence alone does not prove these functions.
- Root works on the new OS through its intended supported mechanism, without
  depending on the stock Android7 root helper. Debloat must retain Google and
  the actual hardware services.

Keep every unperformed functional step explicitly unverified. The parent owns
integration and the hardware test decision; the agents stage individual pieces.
