# Independent stock helper dispatch review

Question: does the exact pinned helper bridge close the prior nested dispatch,
entry-response classification, and pre-entry inverse reporting findings?

Status: review complete. Three prior concrete findings resolved; one P2 decoder-exception boundary defect and one P3 stderr-forwarding omission found. No implementation or live approval.

Outputs: REPORT.md, scripts/replay.py, scripts/adversarial.py, evidence/.
Continuation: rerun the bounded scripts against the recorded production pins;
parent owns every live action. All test files and generated receipts stay here.
Only the exact stock diagnostic 7d74df… and original p10 inverse 902b2f… are in scope.
No physical GO, new kernel, or full-OS assessment is made.

Run from the workspace root with `python3 -B <this-spike>/scripts/replay.py <suite>` for test_faults, test_regressions, test_nested_dispatch, or test_shell_guards. Run `scripts/adversarial.py` and `scripts/provenance.py` with Python -B as well. Adversarial passing assertions include defect reproductions, not blanket safety approval. Review REPORT.md before continuing.
