# Independent final5role terminal restoration design review

Question: does the proposed exact five-role terminal integration preserve the frozen restoration boundaries, and does the exact frozen policy actually authorize DATA?

Status: review complete; integration held. P1: exact frozen policy denies daemon DATA access. P2: the policy-preservation and QA plan must allow only the necessary two-rule future delta and requalify it. This spike issues no approval, target artifact, timing qualification or physical GO.

Outputs: [REPORT.md](REPORT.md) contains prioritized findings and minimal future corrections; `evidence/` contains 69/69 public-input integrity, 23/23 frozen receipt checks, fresh 144-row effective-policy queries and exact binary ioctl/attribute inspection; `scripts/` contains reproducible local inspection only. Darwin memory-limit and old native transition-CLI limitations are explicit in the report/receipt.

[HANDOFF.json](HANDOFF.json) records the hold and correction scope. [binding-review.html](binding-review.html) shows the acyclic dependency order and policy blocker using only self-contained local content.

Scope: local public text/hash/policy inspection, using an already existing native read-only libsepol query. No target execution, compilation/build, new target binary/image, device, ADB, root, SSH, network, cloud, VM, private calibration/keys, reviewed production edits, other-agent/build polling or delegation.

Continuation: read REPORT.md and evidence before implementing in a new parent-owned fork. Preserve frozen two-role image/source/flags. Actual install admissions, final bindings and all physical acceptance remain absent/pending. Do not generate a placeholder manifest hash header or adopt the separate phase-proof optimization.
