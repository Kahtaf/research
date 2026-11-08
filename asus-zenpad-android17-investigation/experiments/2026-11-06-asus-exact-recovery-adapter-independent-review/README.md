# Independent exact recovery adapter review

Question: does the exact recovery-only adapter enforce its offline-testable transport and evidence contract?

Status: complete; one P1 finding. A backward wall-clock adjustment can extend the 180-second USB pin and admit an actual nested candidate dispatch. No execution approval or physical GO.

Important outputs:

- [REPORT.md](REPORT.md): finding, exact source lines, reproduction, smallest fix and limits.
- [HANDOFF.json](HANDOFF.json): exact pins, test results and preservation summary.
- [scripts/targeted_review.py](scripts/targeted_review.py): audit-guarded independent regressions; fresh output directory on every run.
- [evidence/targeted-1794005646847753000/receipt.json](evidence/targeted-1794005646847753000/receipt.json): nine tests, two failures reproducing the same finding, zero errors.
- [evidence/supplied-suite.final.log](evidence/supplied-suite.final.log): 45 supplied methods pass.
- [evidence/preservation.json](evidence/preservation.json): all reviewed files and 16 original inputs unchanged.
- snapshot/: unchanged implementation plus public/fixed-stock input copies. One extra public old-image fixture supports the supplied rejection test. Prior test failures are preserved.

Continuation: parent fixes the freshness guard and regenerates review pins. Re-run only audit-guarded local tests in a new snapshot of the changed code. Existing snapshot tests can be rerun with `python3 -B scripts/targeted_review.py`; the two failures are expected until the code is fixed. Never execute device/helper commands from this spike. Parent owns all eventual physical actions. No device, network, VM, build, private calibration, or key operations occurred.
