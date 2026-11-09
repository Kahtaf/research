# Working notes

Current status: paused by the owner on2026-11-09. STATE-AND-RESUME.md is authoritative. The notes below include historical preparation and execution.

## 2026-11-08 handoff

Owner requested clearing the old goal, stopping background work, reclaiming excessive artifacts, and a new-thread prompt for latest-stable Alpine on the existing stock kernel. No new investigation or flash is being run in this session. Known prior project identified as kaantcp/z380m-alpine; original local source pin and current GitHub HEAD both 7218a276f252a59874ab860683c061fa2b856519.

Closed preparation: 6,250 obsolete/duplicate generated files removed with hash/identity receipts; 17 uncertain images retained. 17.78 GB free-space increase. Old HTTP server stopped; shared ADB and unrelated work untouched. No Alpine or tablet operation performed. Goal Clear UI action queued `/goal clear`; not yet observed applied during the running turn.

## 2026-11-09 pause checkpoint

- Proved native Alpine3.24.4 on the exact stock3.18.35 kernel, first in RAM and then a persistent microSD ext4 loop root. Retained original BOOT/SYSTEM/GPT/bootloader/factory partitions and private stock rollback images.
- Resolved stock WMT readiness/firmware/calibration dependencies, native Wi-Fi/DHCP/HTTPS and pinned SSH. Repeat boots, stock Android return, persistent OS/SQLite data and actual DHCP renewal passed.
- Adapted Goodix to native libinput/XI2; owner confirmed scrolling, pinch and typing. Added automatic Onboard, bottom docking and a separate JWM workarea patch; retained packaged JWM.
- Fixed utility AAC loading with a minimal app-private FFmpeg61 closure and retained sandboxing. A real output experiment exposed a stock ALSA mmap kernel crash; a qualified PulseAudio plain-write bridge avoids it. Muted YouTube playback passed; ordinary speaker output is incomplete.
- Qualified an independent speaker guardian/controller prototype for normal idle and hung-controller cleanup. Added an on-demand speaker-check menu; software playback/shutdown passed, physical browser audibility remains open.
- Parked active accelerometer/MD32 work after exact running binary/source differences and calibration lifecycle gaps were established. No active sensor experiment was performed.
- Confirmed idle resources and automatic CPU hotplug; enabled Firefox reduced motion without changing sandbox/CPU policies. No overall speedup claimed.
- Audited everyday independence: buttons advertise capabilities but lack configured actions, Bluetooth is absent, and cold power/suspend remain unqualified. Current minimal UI does not meet the desired polished tablet experience.
- Researched one Xfce-on-Alpine trial as the next native option, and Android+Termux/X11 as a separate hybrid alternative. Neither was installed.
- Owner paused further development and requested source-only publication. Preserve local private inputs; no tablet operations were sent for this archival task.
