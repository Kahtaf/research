# ASUS BROM recovery access proof

Question: Can this exact P00A_2 reach its MediaTek chip recovery interface and support a verified recovery path independently of working Android?

Status: Preloader READY mode request now enters the exact ASUS fastboot interface without Android. Fastboot queries work and a normal reboot returned to stock Android. Standard BROM/download handshake is not established. Bootloader remains locked; no flashable Android 17 ROM or demonstrated failed-boot storage restore exists. No flash, erase, unlock, download agent or RAM image payload was sent. User authorization to flash once ready persists.

Inputs: Exact-unit critical-area/GPT backups, stock on-demand root, pinned mtkclient source, and primary-author Z380M Alpine BROM/DA logs in the sibling boot-access-audit spike.

Outputs: Guarded access probes, observed identity/security metadata, readback/restore evidence and decision before any custom image is written.

Continuation: Read STATUS.md when available. Preserve normal boot, system, LK, preloader and user data. Do not infer flash/restore ability from handshake success alone.
