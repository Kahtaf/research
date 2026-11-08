# Independent bounded host I/O review

Question: does the copied implementation preserve admission and protocol protections while enforcing caller deadlines and truthful terminal outcomes?

Status: review complete; parent fixes required for this revision's deadline and terminal-outcome contract. Local offline fake fixtures only. No production edits, device operations, usable execution authorization, source admission, or hardware timing qualification. The separate accepted stock-rescue scope is unaffected.

Important outputs:

- [Findings, smallest parent fixes, pins, scope, and continuation](REPORT.md)
- [Baseline: 46/46 tests, all 71 children reaped](evidence/qa.json)
- [Adversarial: 29 cases, 15 preserved failing assertions, all 58 children reaped](evidence/adversarial-results.json)
- [Independent integrity verification](evidence/integrity.json)
- `review/adversarial.py` and `review/readback_peer.py`: new offline harness/peer; `review/verify_integrity.py`: small-input pin/diff checker.

Continuation: read REPORT.md and fix the parent implementation separately. Reproduce from this folder with `python3 -B review/verify_integrity.py`, `python3 -B tests/run_qa.py`, and `python3 -B review/adversarial.py`. The adversarial suite intentionally exits 1 on this unmodified revision. Source/tests/profiles here are byte-exact review copies. All original spikes remain immutable. No actual-device command is supplied.
