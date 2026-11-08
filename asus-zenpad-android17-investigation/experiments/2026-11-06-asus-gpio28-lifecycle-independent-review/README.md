# Independent GPIO28 lifecycle source/host review

Question: does the five-path lifecycle patch close the independent routing PM/private-data lifetime and persistent suspend findings without changing protected analog bodies, ABI, topology, config, or routes?

Status: complete, bounded no new findings. Both prior lifecycle findings close within the pinned source/host scope. Public local offline source and finite host fixtures only. No production edits. Prior source-port, independent-review, and lifecycle-fix spikes remain immutable. The automatically rejected PCM-copy patch is excluded.

Outputs: [report/HANDOFF.md](report/HANDOFF.md) (findings, exact pins, locks and bounds), evidence/ (source audit and host results), scripts/ and tests/ (owned review tooling). Old real-body failures reproduced; corrected 38+12 cases, ten added adversarial cases and 138 readiness calls through all 46 actual guarded registrations pass.

Continuation: read report/HANDOFF.md; `python3 scripts/run_review.py` reproduces checks in this spike only, and `python3 scripts/audit.py` rehashes selected originals/copies. Target ARM64 object/full-kernel builds, integration, and hardware qualification remain separate; no deployment/hardware/physical/flash GO. GPIO cache describes API-reported command success only; lower MTK register errors are lost. Darwin hard one-core/1GiB enforcement is unavailable and documented.
