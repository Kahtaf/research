# Exact r8 continuation

Question: prepare the next incremental full-product continuation from terminal r7, correcting the actual WPA compiler failure, exact zRAM label, and native compiler evidence channel.

Status: sealed and staged for parent review. No r8 production attempt, integration, approval, build or device action was performed. All 27 Linux tests and the final read-only source audit passed. Actual post-delta product dumpvars/build/images/runtime/physical qualification remains unproved.

Important outputs: [HANDOFF.md](HANDOFF.md) contains the exact seal, review surfaces, hash-bound parent r7 acceptance and PLAN_ONLY/parent launch instructions. [REPORT.md](REPORT.md) records genuine compiler/policy results, retained failures and limits. `source/` contains both exact source deltas and the script diff. `inputs/qualification/` and `evidence/` hold compact authentic evidence. `artifacts/` contains the compact export and genuine isolated SDK37 LTO object.

Ownership: `/srv/android/asus-reviewed-build-kit/r8` and `/srv/android/asus-product-integration-staging/r8`; isolated outputs stay under `/srv/android/asus-reviewed-build-kit/r8-fixtures`. Earlier repositories, attempts, logs, cache, images and frozen probes remain in place. Historical local preparation scripts are under `preparation/`; they are not launch entry points and must not be replayed.

Continuation: parent reads HANDOFF.md and complete memory evidence, waits for its separately owned runtime-prerequisite terminal receipt, authors its own exact r7 failure acceptance, runs PLAN_ONLY, and owns any later one-shot PARENT_EXECUTE launch under the original lifecycle flock. Do not replay baseline patches, remove attempt markers, clean cache or claim physical GO.
