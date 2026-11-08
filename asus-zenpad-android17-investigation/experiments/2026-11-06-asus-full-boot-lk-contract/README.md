# Future full BOOT LK contract

Question: can a future full SDK37 BOOT preserve its payload bytes while satisfying this ASUS P00A_2 unit's exact normal-BOOT LK relocation and 99-byte command-line contract?

Status: **implemented and host-tested; PLAN_ONLY by default; parent integration pending**. No actual full AOSP BOOT or physical success is claimed. All generated images are deliberately **NONBOOTABLE synthetic fixtures** containing no `/init`.

Important outputs:

- [REPORT.md](REPORT.md): findings, exact 92-byte header, primary evidence, boundaries and concrete integration steps.
- [HANDOFF.md](HANDOFF.md): concise parent handoff.
- [evidence/replacement.patch](evidence/replacement.patch): two replacements plus the new contract module; not applied to the active target.
- [evidence/checks.json](evidence/checks.json): reproduction results; 26 packaging test groups, two settings of exact-source-body tests, normal-LK audit, integration test.
- `scripts/package_full_boot.py`, `scripts/boot_memory.py`, `scripts/lk_contract.py`: standalone replacements.
- `artifacts/`: two explicitly marked synthetic fixtures using actual r1/product-r3 compressed Image streams and test-only cpio.

Continue by reading REPORT.md and reviewing the patch. Run `python3 scripts/run_checks.py` from this folder for offline reproduction; outputs stay here. Parent owns all device/ADB/root/flashing actions and first-4.9-test nearby fallback. Never install the synthetic fixtures. Old artifacts, frozen R2 transport quarantine, active build sources and nested repositories were preserved.
