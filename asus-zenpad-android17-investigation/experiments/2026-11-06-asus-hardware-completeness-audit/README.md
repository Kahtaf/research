# ASUS P00A hardware completeness audit

Question: What remains between the staged genuine Android17/SDK37 product and usable P00A_2 hardware, and which additional factory state must survive userdata destruction?

Status: Completed read-only source/ELF audit and actionable handoff. 32 offline consistency checks pass. Actual trees captured at 2026-11-06 19:34:08 UTC. No compilation, QEMU, device operation or physical readiness claim. Parent owns all integration and device/private preservation work.

Important outputs:

- `report/HARDWARE-MATRIX.md` — source-cited subsystem matrix, build versus commissioning prerequisites and implementation order.
- `report/CALIBRATION-PRESERVATION.md` — metadata-only parent/private checklist, storage distinctions and explicit completeness limits.
- `report/calibration-records.json` — 71 public stock record definitions, IDs and payload sizes, cross-checked between ARM32 and ARM64. No actual calibration values.
- `report/HANDOFF.md` — concrete next bounded tasks.
- `evidence/verification.json` — 32 passed static checks; no runtime/physical tests.
- `scripts/` — executed read-only inspection and evidence verification.

Continuation: Read HANDOFF and MATRIX. Preserve prior spikes and nested repositories. Keep active r5 source/out frozen. No device/ADB/USB/root/flashing, private calibration/key-content access, cloud lifecycle operation, package installation or build was performed here. The existing SSH key was referenced only as an authentication path. Do not run source-audit scripts as an excuse to expand scope.

Local reproducibility: `python3 scripts/verify_evidence.py`. Remote public-source receipts came through the existing builder SSH into this directory. Selected public ELF copies are in `/srv/android/asus-hardware-completeness-audit/public-selected`; no whole SYSTEM/data image was copied/extracted, and no large image hash was repeated. The remote existing SYSTEM source was already parent-verified byte-identical to the public OEM stream. This audit does not independently requalify that complete source.

Interpretation limits: `details.txt` records an initial attempt that lacked remote rg; `details-r2.txt` is the successful fallback. ARM32 disassembly appended in `nvram-tables.txt` incorrectly decodes Thumb as ARM and is not used; table metadata is independently valid, and corrected ARM64 disassembly is in `abi-details.txt`, with GOT relocations in `final-source-checks.txt`. No stock binary was executed.
