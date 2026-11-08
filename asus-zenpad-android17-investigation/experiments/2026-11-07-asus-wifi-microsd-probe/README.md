# Install the exact microSD-report probe over Wi-Fi

Status: implemented; offline plan checked. No live execution, device contact or flash.

Only candidate50570761 and full-p10 hash78005304 are admitted. Reuses the existing authenticated TCP transport, root helper, exact device/geometry checks, shared lock and full readbacks. The fixed execute sequence is copied byte-for-byte from the earlier reviewed adapter, with only this module’s exact candidate/preimage constants changed. Known prior RAM-probe recovery is allowed; unknown bytes are refused. Transport uncertainty stops all automatic operations. Only recovery p10 is writable, with one bounded original-stock inverse on a known install failure. No reboot.

Run `python3 -B source/install.py` for PLAN_ONLY. Parent may use `--execute` only after Wi-Fi identity is established, card marker is prepared and nearby manual fallback is available. Keep stock Android running while installing; enter Recovery using VolumeUp+Power, then VolumeUp scroll / VolumeDown select. Do not enter stock recovery with the stale wipe request. Normal Android can restore stock recovery, so avoid another normal boot between installation and trial.

Card marker and report contract are in sibling `2026-11-07-asus-linux49-microsd-report/HANDOFF.md`. This is not a full-OS writer or proof of physical boot.
