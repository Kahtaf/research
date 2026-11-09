# Prior Alpine port and release baseline

Verified Nov8,2026. Recheck current release and upstream state at the start of the new session.

- Project: [kaantcp/z380m-alpine](https://github.com/kaantcp/z380m-alpine)
- Observed main HEAD: `7218a276f252a59874ab860683c061fa2b856519`, commit dated Oct21,2026.
- [Pinned guide](https://github.com/kaantcp/z380m-alpine/blob/7218a276f252a59874ab860683c061fa2b856519/docs/GUIDE.md)
- [Hardware status](https://github.com/kaantcp/z380m-alpine/blob/7218a276f252a59874ab860683c061fa2b856519/docs/HARDWARE.md)
- [Changelog](https://github.com/kaantcp/z380m-alpine/blob/7218a276f252a59874ab860683c061fa2b856519/docs/CHANGELOG.md)

The project describes Alpine3.24.2 aarch64 on an unchanged stock ASUS3.18.35 kernel. Published evidence supports base boot and USB networking/package access. The author reports framebuffer Xorg/JWM and touch working; desktop/touch physical logs are not included. Newer dist installers are rig-tested and were not rerun physically. On-screen keyboard/autostart claims are rig-only. Treat donor documentation as a lead, not qualification of this tablet.

Wi-Fi remains absent (`wlan0` missing); upstream has not established the exact missing component. Other peripherals and power management remain incomplete. Donor uses an ELAN touchscreen; this tablet was observed with GoodixGT6108. Its legacy USB gadget and no-devtmpfs startup are important integration details. The guide overwrites BOOT and part of SYSTEM. Do not execute it before reviewing our own recovery state, geometry and rollback route.

[Official Alpine downloads](https://alpinelinux.org/downloads/) showed stable **3.24.4**, released Nov5,2026. Pin the latest stable aarch64 userspace at implementation time. Verify its required syscalls, package workloads and browser behavior on stock3.18; neither successful extraction nor a donor's older release demonstrates that compatibility.

Start with donor review plus our working stock Wi-Fi dependency inventory. Prove a small useful Linux environment before adding desktop complexity. No new kernel port is part of this plan.

Kernel source caveat (verified after experiment55): ASUS official Z380M source listing tops out atV4_7_0 dated2017-01-05. This is NOT the installed Aug2018/V5.3.20 kernel source; binary accelerometer initialization differs and uses SENSORHUB. See reports/sensor-hub-blocker.md. Do not infer sensor callback safety from the older tree or substitute Z380KL/P024 hardware.
