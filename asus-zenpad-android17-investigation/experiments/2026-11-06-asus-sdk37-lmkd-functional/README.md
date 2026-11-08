# SDK37 lmkd functional qualification

Question: does genuine SDK37 lmkd register PSI and handle controlled memory pressure with approximately 2 GiB RAM, MEMCG disabled and 512 MiB lz4 zRAM?

Status: COMPLETE within the native fixture scope, conditional on the staged zRAM file-context correction. Four verified default-policy eviction/recovery cycles pass. A separate protected-incompressible overload failed and is retained. Full Android17 + Google + root footprint and physical tablet usability remain UNPROVED.

Important outputs:

- [Report](report/REPORT.md) and [parent handoff](report/HANDOFF.md).
- [One-line staged label correction](candidate/vendor-file-contexts.additions); not applied to active product sources.
- [Final qualification](artifacts/frozen/evidence/qualification.json), [verified export](evidence/export-verification.json), [actual ELF closure](evidence/elf-runtime-closure.json).
- `artifacts/frozen/`: source pins, real ELF inputs, kernel configuration/delta, commands, complete serial logs, terminal receipts, retained failures.

Continuation: follow HANDOFF using a new fixture revision. Reuse the already completed owned virtual kernel; do not restart builds or reuse run directories. No owned job remains running. Parent owns product integration and all future hardware/framework/GMS qualification. Preserve Android17, Google and root objectives.
