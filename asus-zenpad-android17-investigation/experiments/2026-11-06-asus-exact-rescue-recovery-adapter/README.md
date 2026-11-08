# Exact stock rescue recovery deployment adapter

Question: can the exact reviewed STOCK-only rescue be installed and removed through the guarded stock-Android recovery writer without inheriting false diagnostic attestations?

Status: implementation complete; final offline regressions and source receipt recorded in REPORT.md. No device operation, build, source-kit mutation, rescue connection, activation, mode entry, reboot, or physical approval. Independent build review passed offline; this adapter still needs parent technical review. No physical GO, rescue commissioning, boot, durability, hardware, or full-OS readiness claim.

The fixed candidate is `5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f`, 10,412,032 bytes; its entire zero-padded recovery partition is `3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a`, 16,740,352 bytes. The target has the original SYSTEM/BOOT rescue roles and fixed original-recovery helper. The public target host's unarmed/timing flags do not remove target capabilities. This adapter deploys recovery bytes only, with separate parent-owned supervised manual entry and return and no bounded automatic-return promise.

Important outputs:

- `source/adapter.py`, `source/root_dispatch.py`, dependency `source/engine.py`, and fixed `profile.json`.
- `COMMANDS.md`: offline commands and deliberately non-executing future parameter shapes.
- `REPORT.md`, `HANDOFF.json`, `evidence/source-receipt.json`, and `evidence/diffs/`: implementation decisions, exact pins and reviewable changes.
- `evidence/offline-*/`: audit-guarded tests, retained failures, and modeled scenario receipts. These are not physical captures.
- `evidence/original-inputs.{before,after}.json`: original public source/image/stock-recovery preservation.

Continuation: parent reads REPORT, exact source receipt, diffs and latest test receipt; independently reviews the adapter. Future actual operations belong to the parent. The supplied template is unapproved, has no validity interval, and asserts no person's presence. Parent must supply a genuinely reviewed fresh bounded phase contract and truthfully attest current supervision and nearby Power fallback, then obtain an actual same-run pin through the adapter. Parent must retain the receipt nonce from the successful live install return for later removal; a visible journal alone cannot reconstruct completion. Install and restore have separate exclusive phases; each pin must stay fresh through actual nested command dispatch. Manual return is separately observed by the parent, followed by a fresh healthy-stock/USB pin for removal. An expired, failed, or uncertain run is consumed; do not resume, retry, create a new UUID to bypass uncertainty, reconnect, or infer success from a receipt or later stock observation.
