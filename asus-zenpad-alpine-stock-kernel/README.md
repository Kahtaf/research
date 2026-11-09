# ASUS ZenPad Z380M: Alpine on the original kernel

**Paused by the owner on 2026-11-09.** This is a source-only research checkpoint, not an installable image or a finished tablet distribution. Start with [STATE-AND-RESUME.md](STATE-AND-RESUME.md).

The question was whether current Alpine aarch64 could make this ASUS Z380M/P00A_2 useful as a touchscreen dashboard, browser and small SSH server while retaining its exact stock Linux3.18.35 kernel. The tested userspace is Alpine3.24.4. Work began from [kaantcp/z380m-alpine](https://github.com/kaantcp/z380m-alpine), pinned to `7218a276f252a59874ab860683c061fa2b856519`, and adapted to this tablet's Goodix panel and stock Android Wi-Fi dependencies.

## What actually worked

- Independent microSD boot from a persistent2GiB ext4 file, with repeat ordinary reboots, stable SSH identity and persistent Python/SQLite workloads.
- Cold stock MediaTek WMT initialization, native Wi-Fi association/DHCP/HTTPS and key-only SSH. A real DHCP renewal also passed.
- Xorg/fbdev desktop, Firefox ESR140.12, native Goodix one-finger scrolling and pinch zoom, and an automatic bottom keyboard. The owner physically confirmed gestures, typing and hiding; keyboard work-area resizing also passed.
- Private decoder-only FFmpeg libraries fixed the reproduced Firefox AAC crash while retaining the separate utility sandbox. A real muted YouTube sample played; this is not a claim that all media works.
- A safe PulseAudio plain-write path avoids a real stock ALSA mmap kernel crash. An independently guarded speaker prototype passed normal and hung-controller shutdown checks. The owner heard an earlier direct speaker tone; normal browser sound is not enabled or physically confirmed.
- Stock Android return was demonstrated. Original BOOT/SYSTEM, bootloader, GPT and factory partitions were preserved; stock rollback images remain local.

## Why it is paused

The installation falls short of the owner's desired polished, independently functional tablet. Buttons have declared kernel capabilities but no configured desktop actions; Bluetooth is not brought up; ordinary speaker integration, cold power-on and suspend/resume remain incomplete. Automatic rotation is parked because the running2018 sensor-hub driver differs from the retained2017 source and lacks a qualified calibration-preserving lifecycle.

The latest recommendation is [one reversible Xfce-on-Alpine trial](reports/interface-recommendation-2026-11-09.md), rather than more work on the minimal JWM UI. No Xfce/LXQt/Phosh switch was performed. Android with Termux/Linux tools is a separate, untested hybrid alternative if Android's hardware integration is the priority. Android17 and Linux4.9 remain parked.

## Where to pick it up

- [State, private prerequisites, safety boundaries and resume steps](STATE-AND-RESUME.md)
- [Current detailed memory](MEMORY.md) and [research notes](notes.md)
- [Everyday-use completion plan](reports/INDEPENDENT-USE.md)
- [Hardware/boot operating instructions](reports/OPERATING.md)
- [Upstream pins and source caveats](UPSTREAM.md), [source preservation](SOURCE-PRESERVATION.json) and [external inputs](BUILD-INPUTS.md)
- [Archive inventory](ARCHIVE-MANIFEST.json); run `python3 tools/check-archive.py` to verify it without contacting a tablet

`reports/` and `evidence/` preserve dated findings, including superseded failures. `scripts/` contains historical experiment/build/deployment code, not a run-all installer. `overlay/` contains adapted integration files and focused patches. Only specifically authored source/validation helpers are retained under `sources/`; fetched repositories and complete upstream source trees are omitted.

This Git checkpoint excludes credentials, calibration, stock firmware/backups, browser data, disk/rootfs images, compiled libraries, media fixtures, downloads, build trees and nested Git repositories. Those local inputs are not backed up by this repository. No new tablet operation or firmware write was performed while preparing this pause checkpoint.
