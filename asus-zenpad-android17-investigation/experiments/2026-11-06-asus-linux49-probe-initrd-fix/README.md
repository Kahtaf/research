# Correct the exact LK ramdisk handoff

Question: can the r2 packaging conflict be corrected without changing compiled
kernel code, diagnostic userspace, policy, keys, or any hardware operation?

Status: corrected r3 built and replayed through the pinned LK semantic model.
The old r2 install entry point is structurally quarantined. The matching LK strips
the MTK wrapper and relocates the compressed ramdisk to 0x44000000; r2's explicit
initrd argument incorrectly selected 0x44000200. See the exact binary audit in
`../2026-11-06-asus-lk-linux49-handoff/REPORT.md` and its 14 replayed checks.

This new revision changes only the Android header's initrd token and the three
chosen DT properties. Compressed Image and complete wrapped ramdisk must remain
byte-identical to r2. All other compiled DT properties/reservations are checked.
No device, network, kernel compilation, or active build source operation occurs.

Run `python3 -B source/build.py` to create a new `artifacts/probe-r3` directory.
Existing output is refused. All outputs are UNTESTED physically. The new exact
observer/transport pins must be integrated and reviewed before a supervised test.
The original r2 artifacts and original audit evidence are preserved.

New artifact: `artifacts/probe-r3/UNTESTED-combined-linux49-ram-probe-r3.img`,
8,880,128 bytes, SHA-256
`45551fec6af489bef6813131fb3854eddcfe95d3ca3fa640fea7a37dfd21b630`.
Full p10 zero-padded SHA-256:
`01d7bbb4d8951875f753fde2c1f7fb486dec1e42bd502b6b93a5296245fe9bf3`.

Actual modeled initrd is now 0x44000000 through 0x4411f7b0, with gzip magic at
its first byte. Header length 95 fits the measured LK 99-byte content limit.
Compressed Image and entire wrapped ramdisk are unchanged; only the header
token/checksum and three DT chosen properties changed. See manifest.json,
evidence/r3-handoff-model.json and evidence/parent-correction-receipt.json.

This is host/static proof, not physical execution. The full Android BOOT packager
also needs the relocation correction and a compact LK-compatible command line.
The speculative stock-rescue 2 MiB DT-token clamp was refuted by the same audit:
LK replaces the original DT bootargs and writes actual payload bounds. Final
armed rescue packaging still needs exact size/layout review.
