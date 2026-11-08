# Independent exact-LK recovery restoration review

Question: can the exact locked ASUS P00A LK restore the original full recovery p10 without working Android userdata?

Status: review in progress; offline only. Parent explicitly includes intrinsic p10 TRIM in the fixed-original restoration candidate. No physical GO, device operations, writer implementation, arming, private payload access, build changes, or installations.

Outputs: `REPORT.md` (final review), `evidence/` (replay, hashes, adversarial fixtures), `source/` (byte-identical copied author harness plus isolated review fixtures).

Continuation: use only the existing `../2026-11-06-asus-stock-userdata-recovery/.venv/bin/python -B`. Original sources and receipts remain unchanged. Parent owns all device actions and approval. See final report for remaining qualification gates.
