# Coherent runtime capture preparation v6

Question: can the public-source parser model Ninja 1.12.1 own/build/enclosing environment semantics and reject unsupported effective dyndep while applying the parent's exact duplicate-producer correction?

Status: implementation and bounded Linux fixture QA complete; independent review pending. Immutable VM sibling: `/srv/android/asus-official-runtime-capture/preparation-v6`. No real capture or graph qualification occurred. V5 and its review remain preserved.

Important outputs:

- `REPORT.md`, `REVIEW-PACKET.md`: behavior, evidence, review targets and continuation.
- `minimal-v5-v6.patch`: three-file production delta.
- `inputs/ninja-1.12.1-pins.json`: upstream commit/source pins.
- `tool-pins.json`, `runtime-pins.json`, `HANDOFF.json`, `FINALIZED.json`: final seal and hash binding.
- `evidence/`: inherited 115, new 35, review 23, exact parent before/after four-case receipts, static preservation and resource correction.

Limits: serial one CPU, 1 GiB address space, finite CPU/wall, <=128 MiB new owned allocation. Only public snapshots, static v5 source and small synthetic fixtures were used. No old VM index, active source/output/kit/R9, native engine or device access occurred.

Continuation: follow the verification and default-plan commands in REVIEW-PACKET.md, then arrange independent review. A future parent must use a new preparation sibling for an exact SHA-bound real build profile after genuine terminal success. This sealed preparation keeps the failed-R8 default and grants no capture, metadata admission, runtime readiness or physical authorization.
