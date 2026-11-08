# Full SYSTEM read-only observer preparation

Question: Can a fixed-path guest observer and fail-closed admission/generation interface be prepared and tested without consuming an unfinished product?

Status: Complete: observer/interface implemented and fixture-only positive/negative QA passed. No real SYSTEM admitted, captured or mounted; no physical/flash GO.

Outputs: [REPORT.md](REPORT.md), [acceptance.json](acceptance.json), [PARENT-COMMANDS.md](PARENT-COMMANDS.md), `source/` observer/resolver TUs, `scripts/` interfaces, `tests/` fixture QA, `contracts/` strict parent receipt definitions, and `evidence/` pins/serials. Large files remain at `/srv/android/asus-full-system-observer-preparation-20261106`; accepted final fixture runs are `runs/strict-{positive,wrong-hash,wrong-metadata}`.

Continuation: Read REPORT.md and PARENT-COMMANDS.md when complete. Preserve the prior `2026-11-06-asus-sdk37-system-ext4-qualification` spike and all prior fixtures. Never reuse fixture-only receipts for production. Production defaults to PLAN_ONLY and requires an externally pinned parent admission with terminal host validation, coherent content/metadata/source receipts and the owner raw path.

Local verification: `python3 -B scripts/finalize.py`. Historical setup/QA scripts refuse fresh-directory reuse and must not overwrite any preserved attempt. The runtime observer is tested; genuine host metadata producer compilation/execution and real product admission remain parent-owned pending contracts.
