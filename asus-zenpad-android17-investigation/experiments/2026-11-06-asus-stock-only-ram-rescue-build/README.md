# Original STOCK-only RAM rescue candidate

Question: can the reviewed fixed original-p10 restorer be independently packaged with the exact original SYSTEM/BOOT manifest and corrected host completion contract?

Status: **OFFLINE BUILD AND REPRODUCTION COMPLETE — STOCK-ONLY/UNAPPROVED.** The target has two original manifest records. Public host `ARMED=False` and `TIMING_QUALIFIED=False`; no execute/physical approval. No tablet contact occurred.

Start with [HANDOFF.md](HANDOFF.md) and [REPORT.md](REPORT.md). Important outputs are the [new candidate](artifacts/candidate/UNAPPROVED-STOCK-ONLY.img), [unapproved session contract](artifacts/candidate/session-contract.UNAPPROVED.json), source/tests, inventories and evidence. [BUILD.md](BUILD.md) explains offline reproduction; [PROTOCOL.md](PROTOCOL.md) states completion and UNKNOWN rules.

Owned remote fixture: `/srv/android/2026-11-06-asus-stock-only-ram-rescue-build`. Full padded p10, original recovery payload copy and fixture initramfs remain there. This Mac delivery is compact; no full SYSTEM/data copy/hash was made.

Continuation: parent independently reviews these exact pins and then separately owns read-only physical/timing commissioning, any later reviewed qualification revision and explicit physical approvals. Do not toggle the existing flags, alter sealed artifacts, rerun creation into the existing fixture or infer physical readiness. Existing input artifacts remain byte-identical. No offline implementation blocker remains.
