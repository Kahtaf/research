# Stock init-mediated roundtrip continuation

Question: can the fixed stock-only controller safely distinguish a qualified one-shot roundtrip from incomplete or uncertain outcomes?

Status: **implemented; 65 offline fault tests and seven extracted init/adbd emulation cases pass; parent technical review pending**. The real local plan validates the pinned candidate and backup receipt. PLAN_ONLY remains the default. No device contact, physical GO, presence claim, review approval or active-build operation occurred.

Important outputs:

- [HANDOFF.md](HANDOFF.md): exact local plan and future parent commands, changes, outcome semantics and qualification limits.
- [source/service/controller.py](source/service/controller.py): guarded controller with verified new-stock-return requirement, bounded single inverse and metadata rechecks.
- [tests/service/test_faults.py](tests/service/test_faults.py): typed offline fault fixtures, actual state-machine/observer tests and 30 transport-loss points.
- [evidence/service/qualification.json](evidence/service/qualification.json): machine-readable result and exact limits.
- [evidence/service/latest-fault-suite.txt](evidence/service/latest-fault-suite.txt), [evidence/service/firmware-emulation.json](evidence/service/firmware-emulation.json): passing results. Timestamped reports retain earlier failures.
- [evidence/service/continuation.patch](evidence/service/continuation.patch), [evidence/service/inherited-evidence-index.json](evidence/service/inherited-evidence-index.json): changes and preserved input provenance.

Continuation: parent reviews the concrete handoff and the unapproved generated template. Parent alone owns all live operations, shared integration and fallback readiness. The inherited window remains 2026-11-06 17:03–23:03 UTC; elapsed time is not evidence of user presence. Do not extend the window or select a new 4.9 image. The prior direct-shell RESTART2 denial remains historical evidence for a different entry route. No Android 17, Play/Services, persistent-root or hardware-readiness claim is made here.

Prior files and nested repositories are preserved. No full SYSTEM/data images were copied, no large-image rehash was performed, and no builder connection was needed. All new outputs are in this spike.
