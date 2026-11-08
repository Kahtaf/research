# Independent re-review of parent stock-roundtrip fixes

Question: do the exact parent fixes resolve the three earlier findings, including generated shell and nested dispatch/exception boundaries?

Status: complete. One P1 nested-helper expiry gap and two P2 issues reproduced. Offline only; no device, network, cloud, build, live approvals, or existing-source edits. See [REPORT.md](REPORT.md).

Outputs: REPORT.md (final findings), evidence/ (fresh replay and adversarial receipts), scripts/ (reproduction runners), tests/service/ (byte-identical parent test copies).

Continuation: parent owns implementation and any live decision. Re-run only documented offline runners here. Production imports come directly from the parent-fixes source; copied tests relocate their temporary files and receipts into this spike. Never invoke production main with execute. No private payloads or large image copies are needed.

Reproduce from the workspace root:

```sh
python3 -B 2026-11-06-asus-stock-roundtrip-fixes-rereview/scripts/replay.py test_faults
python3 -B 2026-11-06-asus-stock-roundtrip-fixes-rereview/scripts/replay.py test_regressions
python3 -B 2026-11-06-asus-stock-roundtrip-fixes-rereview/scripts/replay.py test_shell_guards
python3 -B 2026-11-06-asus-stock-roundtrip-fixes-rereview/scripts/adversarial.py
python3 -B 2026-11-06-asus-stock-roundtrip-fixes-rereview/scripts/shell_review.py
2026-11-06-asus-stock-programmatic-control/.venv/bin/python -B 2026-11-06-asus-stock-roundtrip-fixes-rereview/tests/service/test_firmware.py
python3 -B 2026-11-06-asus-stock-roundtrip-fixes-rereview/scripts/verify_provenance.py
```

These commands rewrite only this review's final receipts. Preserve them first if making another independent review. `adversarial.py` passing means the documented defects reproduced, not that their safety conditions passed. The captured `evidence/generated-write-helper-script.sh` is for inspection and syntax checking only: **do not execute it**. Firmware tests remain stub-boundary evidence. Parent must fix/review the findings and make its own fresh decision; this spike grants no live approval.
