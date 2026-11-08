# Exact R3 recovery transport

Question: can the corrected R3 RAM probe use the guarded recovery transport and strict observer while the obsolete R2 remains un-installable through the supported CLIs?

Status: implemented and verified offline. Two independent final replays passed 60 tests each. The R3 image and manifest reproduced byte-for-byte. PLAN_ONLY is the default; physical boot and hardware readiness are unproved.

Important outputs:

- [REPORT.md](REPORT.md): scope, exact pins, evidence, limitations and physical gate.
- [COMMANDS.md](COMMANDS.md): concrete parent review/replay and guarded execution commands.
- [profile.json](profile.json), [source/probe_transport.py](source/probe_transport.py), [source/observer.py](source/observer.py): exact R3 entry and observer.
- [source/recovery_control.py](source/recovery_control.py): inherited engine; only staging BASE changed.
- [source/reproduce.py](source/reproduce.py), [reproduction receipt](evidence/reproduction/receipt.json): pinned metadata reproduction, unchanged kernel/ramdisk, all 22 cpio entries.
- [code receipt](evidence/code-receipt.json), [source freeze](evidence/source-freeze.json), [implementation diff](evidence/implementation.diff), [R2 quarantine receipt](evidence/r2-quarantine.json).
- [first replay](evidence/final-replay-1/receipt.json), [second replay](evidence/final-replay-2/receipt.json): process-blocked tests and detailed scenario errors.

Continuation: parent reviews REPORT.md, exact code/profile receipts and COMMANDS.md. Parent alone owns every device operation. Keep the source/profile/observer frozen during a run. The first physical Linux 4.9 test requires actual nearby fallback and current supervision; no arrival-time estimate is approval. Preserve the old R2 quarantine and historical artifacts.

Offline checks, from this folder:

```sh
python3 -B tests/run_tests.py
python3 -B source/probe_transport.py verify-local
python3 -B source/probe_transport.py plan
python3 -B source/observer.py verify-image
```

Each test invocation writes to a new directory under evidence. No subprocess/device operation is allowed inside tests. All new outputs stay in this spike; no SYSTEM/data copy is needed. Full OS porting is outside this unit.
