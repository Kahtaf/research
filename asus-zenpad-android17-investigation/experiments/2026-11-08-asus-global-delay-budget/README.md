# Global __delay iteration-budget diagnostic

Question: can a single global __delay invocation reaching a diagnostic ceiling be identified without early return or changing normal delay read/comparison/YIELD semantics?

Status: **bounded preparation complete; no physical GO or device contact.** The actual r3 audit admitted one diagnostic build. One kernel make at -j8 succeeded, one genuine recovery-only candidate was packaged, and one isolated main() PLAN passed. The exact existing VM is verified TERMINATED and the owned SSH master is closed. No build repair/retry or next variant occurred.

The ceiling is 2^24 = 16,777,216 completed continuing iterations per invocation. Exhaustion explicitly dumps the stack and panics with fresh kernel identity, original start/last/requested cycles, iterations and caller symbol+offset. Normal return still depends only on the original unsigned start-relative condition, with one original-route condition read per loop and YIELD. No extra counter reads or loop logs. The budget has no elapsed-time interpretation and can catch a legitimate long delay. Bare %p is hashed in this kernel; caller_symbol=%pS and the backtrace provide interpretable caller evidence against the exact map. Publication and automatic physical return are not guaranteed. CONFIG_PANIC_TIMEOUT=1 remains unchanged.

Kernel UUID: `a4e847a5-f502-4562-8e6a-c9a358e3f22f`. Helper UUID explicitly reused: `a60fca94-e760-4ce5-a790-5c9a818ce406`. The exact profile binds these distinct identities to one full image. Helper source/binary and complete ramdisk, resolved config, DT/hardware statuses and bootargs remain byte-identical to r3. Source comparison of 62,232 files found only __delay and the fresh entry-tag metadata changed. Common installer execute/Transport/Guard and adapters are unchanged. Only owner-supplied current full-p10 preimage `9939e802ab349dd01fe5ab9c643f2ce0d3219846e3f54513a9b1e9982146965c` was appended.

Important outputs:

- [Candidate](artifacts/candidate.img): SHA256 `578c1c5d57f607a3c93e49ae4bf2a8a2e9a56ed99f74de70bb895e64a9982f21`, 3,567,616 bytes.
- [Full p10](artifacts/candidate.p10.raw): SHA256 `b3ff63a119f791e8d38ab75d2586aba52cf77086026cdfb7ff3fab706d1474c1`, 16,740,352 bytes.
- [All exact pins](PINS.md), [source diff](source/kernel.diff), [installer diff](source/install.diff), [conversion/budget audit](evidence/audit-decision.json), [linked instruction proof](evidence/linked-instruction-proof.md), [packaging receipt](evidence/packaging-receipt.json), [isolated PLAN limits](evidence/plan-isolation-receipt.json), [completion receipt](evidence/completion.json).
- [Parent commands and physical outcome contract](PARENT-HANDOFF.md).

Continuation: parent reviews these exact artifacts and independently owns any one later physical trial. The worker's PLAN used only public code and the r3 diagnostic image as a header fixture; real private stock/root/current-target guards were not exercised. No stock payload was read. Parent's real PLAN retains all inherited checks. The prior cached PC was unproved-epoch r3 __delay+0x44 CMP, not MRS. Missing exhaustion is UNKNOWN, never a negative; fail-stop does not predict subsequent compute completion. No variant, repeat build, physical trial or Android17 flash follows automatically. Experiment 3 remains open until all actual compute/timer/fresh-stock-return criteria pass.

The preserved remote prefix is `/srv/android/asus-global-delay-budget-20261108` with independent source/out copies, native log and caches. Ancestors and prior failures/cache remain intact. No hardlinks, clean, manual timestamp/.cmd changes or resource/time caps were used. Generated compile.h naturally retained the r3 timestamp; UUID/full-image binding provides identity. Resume only with a new explicit parent decision, not by rerunning guarded one-shot scripts.
