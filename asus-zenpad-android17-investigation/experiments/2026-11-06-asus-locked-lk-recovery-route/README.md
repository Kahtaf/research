# Exact locked LK recovery restoration audit

Question: Can this exact ASUS Z380M/P00A_2 locked LK restore original recovery p10 independently of functioning Android userdata?

Status: **Offline audit complete. OEM-assisted path exists; physical qualification pending. Intrinsic whole-p10 TRIM means it fails a literal no-erase requirement.**

Ordinary flash with the session flag clear is denied before image verification. Exact `getvar:sofia_support` sets a RAM flag that admits the raw recovery writer without unlocking or an image-signature/TEE check on that path. It is not a read-only query. Full original bytes reach the writer, but LK attempts whole-p10 TRIM first and ignores its result. No device operation or writer implementation was performed.

Important outputs:

- [REPORT.md](REPORT.md): exact addresses/callgraph, scope, negative cases, conditional parent same-stock qualification and RAM-only fallback prerequisites.
- [HANDOFF.json](HANDOFF.json): machine-readable verdict and next action.
- [31 original instruction cases](evidence/emulation.json), [1,444 verified instruction pins](evidence/instruction-pins.json), [input hashes](evidence/input-pins.json), [registration](evidence/registration.json).
- [Callgraph](evidence/callgraph.html), [executed disassembly](evidence/executed-disassembly.txt), [checks](evidence/checks.json).

Continuation: reproduce the three commands in REPORT.md, then parent reviews the intrinsic p10 TRIM scope before any same-stock write/full readback qualification. No physical GO or arming is supplied. Existing RSC policy remains unchanged; p20 belongs only to the already-reviewed later OEM reset. This audit does not block the first R3 RAM-only kernel trial, which still needs a nearby fallback.

All writes stayed in this new spike. Earlier artifacts/nested repositories, active builds and cloud resources were untouched. Private preservation payloads and security/calibration/key contents were not read; no full SYSTEM hashing/copy occurred. Reuse the existing userdata-recovery Python environment read-only; no installation is necessary.
