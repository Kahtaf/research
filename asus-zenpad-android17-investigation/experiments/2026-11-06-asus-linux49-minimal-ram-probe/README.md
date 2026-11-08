# Linux 4.9 minimal RAM probe

Question: can the exact precompiled physical Linux 4.9 kernel reach static PID1, tmpfs and a read-only configfs USB mass-storage report?

Status: actual static ARM64 build and offline qualification complete; no device operations or physical success. Read HANDOFF.md for exact hashes and limits.

Outputs: source/init.c, scripts/build.py, artifacts/candidate.img and evidence receipts. The padded p10 remains on the builder.

Continuation: read HANDOFF.md and evidence/manifest.json. No deployment adapter or authorization is included. Build only inside the owned remote fixture using scripts/local_driver.py; never alter frozen inputs.
