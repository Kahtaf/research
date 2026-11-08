# Bounded full-install host I/O

Question: can the copied RSC1 client and SOURCE1 host pipe boundary stop within explicit parent budgets while preserving wire bytes, source protections and target uncertainty?

Status: implemented; 46/46 offline tests passed, all 71 children reaped; awaiting fresh independent parent review. HOST ONLY / PLAN_ONLY. Unknown install SYSTEM/BOOT remain UNBOUND_REFUSED. No runtime or flash GO.

Important outputs:

- [Report and Darwin limits](REPORT.md)
- [Reviewable host source diff](evidence/host-io.patch)
- [Original pre/post pins](evidence/prepost-pins.json), [new code pins](evidence/code-pins.json), [changed-file pins](evidence/changed-code-pins.json)
- [Finite behavior QA](evidence/qa.json), [test log](evidence/qa.log), and retained [legacy stall reproduction](evidence/legacy-actual-client-pipe-stalls.json)
- `source/` implementation and `tests/` owned fake peers; original pinned client/manifest and compact profiles are unchanged copies.

Continuation: read REPORT.md and the diff, verify pins with `python3 -B source/verify_handoff.py`, and reproduce offline QA with `python3 -B tests/run_qa.py` from this directory. The parent owns fresh independent review, all future metadata/profile/budget/USB binding, arming and physical commissioning. No actual image, target, network or builder operation is part of this spike.
