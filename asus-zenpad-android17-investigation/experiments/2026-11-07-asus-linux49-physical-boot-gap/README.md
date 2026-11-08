# Physical Linux 4.9 startup gap

Question: Does the compiled e9 kernel's earliest hardware/entry contract differ
concretely from the stock 3.18 kernel that reached the static SD-report PID1?

Status: complete (2026-11-07). One compiled APXGPT clock-input mismatch was
proved, but no causal startup diagnosis is supported without an early execution
record. No device operations, builds, package variants, or prior-artifact edits
were performed.

Outputs: [REPORT.md](REPORT.md) states the supported finding and smallest next
step; `evidence/`, `source/`, and `scripts/` retain the narrow reproducible
comparison and explicitly selected public source files.

Continuation: read REPORT.md and the two prior handoff/initrd-premise reports
before doing anything further. Do not reopen the refuted fixed 2 MiB or wrapper
offset premises. A missing SD/USB report does not establish Linux execution or
locate the physical failure.
