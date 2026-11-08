# Independent offline USB observation correctness review

Question: does the pinned read-only USB observation adapter enforce its dispatch, transport and completion contract?

Status: completed; request changes for the pinned revision. P1: binding can expire during the final guard and still dispatch. P3: README recipe uses a nonexistent source-pin attribute. No production edits or physical GO. Local offline work only, sequential; fake children/regular files/AF_UNIX socketpairs only. No real ADB execution, network, device, root, SSH, cloud or builds; no private calibration or keys.

Inputs: hash-bound byte copies in `snapshot/`; `evidence/inputs-before.json` binds every original input to its copy. Source pin: `bcb3d7c6f6b823491f8fe2a115b72549139b0f2d315e4cf8de620d1e6bb90146`. Snapshot host ADB is non-executable and is used only as hash input.

Outputs: `REVIEW.md` contains prioritized findings, minimal parent fixes, tested protections and limits. `scripts/run_review.py` runs the guarded snapshot suite. `evidence/tests.log` records32 supplied +15 independent passing checks (including defect reproductions); `evidence/freshness-final.log` and `evidence/reproductions.json` contain the final1.5second freshness reproduction. `evidence/reproductions-initial.json` retains both original findings. `evidence/unchanged-and-audit-receipt.json` confirms all19 original and snapshot files unchanged and19 exact80-byte requests. Large per-test binary fixtures were hashed and deleted after each case to keep disk use bounded.

Resource result: parent peak694,452,224bytes; conservative parent plus two child peaks747,864,064bytes, below1GiB. Darwin rejected AS/DATA/RSS hard-limit settings; effective limits and both initial harness failures are recorded. No hard address-space ceiling is claimed. Tests use a60second CPU ceiling and no parallel workers.

Continuation: read `REVIEW.md` and evidence. From this review directory, run `python3 -B scripts/run_review.py` for the full guarded suite or add `--only-freshness` for the focused reproduction. A rerun creates new fixture directories and replaces the summary files; preserve existing evidence first if needed. Any parent fix requires a separately pinned revision and another review. Physical commissioning and timing remain out of scope.
