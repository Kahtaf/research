# Opus PMIC wait audit

Question: does the scoped configured battery/AUXADC/PMIC path establish a self-blocking wait, and does standard detector advice improve the next experiment?

Status: **one bounded source-only review complete; STOP**. No demonstrated current-path IRQ-off/jiffies deadlock; conditional clock-dependent polling found in baseline transport. Recommend one separately authorized trial of the existing cold devkmsg return-boundary candidate.

Outputs: [report](REPORT.md) (under 1,000 words), [full file/slice SHA256 pins and ancestry limits](SOURCE-PINS.json). Scope A inspected 12 distinct production paths; scope B inspected only detector/filter feasibility slices and build/config metadata. Existing public consultation, handoff and source receipts supplied context. No device, ADB, root, private raw logs, VM, network/cloud, builds, tests, source corrections, or children. Original files were read only; outputs are confined to this spike.

Continuation: parent reviews the single recommendation and existing handoff. No automatic trial, deployment, fix, new recorder, detector configuration, or further audit is authorized here. Missing current transport/backend identity remains an explicit limitation, not a reason to expand this review.
