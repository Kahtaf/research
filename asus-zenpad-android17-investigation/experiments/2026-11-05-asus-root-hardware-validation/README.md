# ASUS temporary root and hardware validation

Question: Can this exact ASUS P00A_2 obtain verified root without flashing, while preserving working hardware and Google components?

Status: Repeated on-demand UID 0 root is verified; SELinux is restored to Enforcing after each completed root session. Stock Wi-Fi/internet and Bluetooth discovery pass. Charging diagnostics look normal. Physical touch coverage, Bluetooth pairing/audio and new-kernel hardware operation remain untested. No persistent root daemon or boot/system modification was installed.

Inputs: Stock WW 5.3.20; 16 independently verified device-area backups in the sibling boot-access-audit spike; authorized ADB serial DEVICE_SERIAL_REDACTED.

Outputs: Root method/provenance, bounded attempt logs, hardware baseline and post-root comparisons. Persistent root and any custom-kernel runtime require separate verification.

Continuation: Read STATUS.md when available. Preserve bootloader/preloader and all Google components. Do not use the ZIP scatter as the live flash map.
