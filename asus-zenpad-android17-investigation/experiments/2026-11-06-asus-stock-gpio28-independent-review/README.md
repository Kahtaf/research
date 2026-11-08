# Independent GPIO28 source-port review

Question: does the exact UNQUALIFIED GPIO28 software-contract port preserve the pinned physical BMC configuration and unrelated behavior, handle ownership/lifetime/faults correctly, and compile as isolated ARM64 affected objects plus board DTB?

Status: **CHANGES REQUESTED**. A new codec-private-data teardown permits a NULL dereference through the independent routing PM callback; full reprobe also leaves stale suspend state. Both are reproduced. Genuine isolated ARM64 codec/GPIO/AFE objects and the board DTB compiled successfully before the blocker was discovered. No further target compilation followed. No candidate source fix is authorized or performed here. HAL routes remain unqualified. No hardware or full-kernel approval follows.

Owned remote prefix: `/srv/android/asus-stock-gpio28-review-20261106-r1`. All source copies and Kbuild output must live under that prefix; no hardlinks or Git worktrees. Remote commands are serial, one CPU, 1 GiB address-space limit, finite wall/CPU limits, and at most 4 GiB owned storage.

Important outputs: `report/HANDOFF.md` (final findings and disposition), `evidence/` (commands, original/candidate pins, patch replay, independent tests, compilation receipts), `scripts/` (review reproduction). Read the final handoff before continuation. Never rerun an initialization or overwrite failed attempts. Existing candidate, source, output and frozen artifacts are read-only.
