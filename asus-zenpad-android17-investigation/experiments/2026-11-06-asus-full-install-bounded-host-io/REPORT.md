# Host-only bounded I/O revision

Status: implementation complete, offline QA complete, awaiting the parent's fresh independent review. Default PLAN_ONLY. Unknown install SYSTEM and BOOT remain UNBOUND_REFUSED. No runtime/flash GO, approval file, execution authorization, actual source-profile admission, or physical timing qualification is supplied.

This is a distinct spike from the accepted 80-byte READONLY observer transport (27b8...), exact p10 deployment (24196...), and real recovery restorer. Those implementations and all old artifacts were left untouched. The parent stall reproduction and its JSON are retained under `evidence/legacy-*`.

## Review surface

`evidence/host-io.patch` is the unified source diff against `2026-11-06-asus-rescue-remote-source/source`. Existing behavioral edits are confined to the copied parent adapter, source client, and source pipe boundary. `bounded_io.py`, `bounded_client.py`, and `local_pipe_worker.py` implement the new boundary; the verifier is review support. Tests are separately pinned in `evidence/code-pins.json`.

`worker.py`, `pinned.py`, `journal.py`, `original/client.py`, `original/manifest.py`, and every compact profile/chunk export remain byte-exact copies. The original client's SHA256 remains `0072398a0aa2da83bdf176d672e7ec767b6aaf034892fb603054a22549c5bf69`. The original pin loader still enforces its original client/manifest pins. The offline verifier also preserves the original external rescue client/parent/manifest/common-header pin checks. No image bytes were read, copied, or hashed from existing artifacts. Only tiny newly owned fake images are exercised by QA.

`input-pins.json` records the original small inputs. `prepost-pins.json` records their before/after equality. `changed-code-pins.json` gives pre/post hashes per edited source file, and `code-pins.json` pins every Python implementation/test file. The new `code-pins.json` SHA256 is `f8e480d01c3591ada98343137379cf78d10a4a7075c15d309360f88755784f05`. Local pin verification is evidence, not a trust or authorization root: the parent must independently review and externally bind the new code pins before any eventual use.

## Deadline policy at the caller boundary

There are no default source/target I/O timeouts. Execute parsing requires an independently hash-pinned caller budget document, alongside the unchanged existing contract/manifest/ADB pins. Its only fields are `phases` and `host_child_cleanup_seconds`. `phases` must contain exactly `source_preflight`, `control`, `reconciliation`, `transfer`, and `whole_image_hash`, each a pair of explicit positive finite phase/message seconds. No usable policy document is shipped. Tiny timings inside tests are fake-fixture policy only.

The parent creates each phase once with `monotonic() + phase_seconds`. Each request derives a single absolute message deadline, capped by that absolute phase deadline. Request header, payload, reply header and payload use that same deadline. Partial progress, interrupted syscalls, successful short writes, repeated readiness notifications and slow drips never extend it. A standalone incoming frame receives one deadline covering its whole header and payload. Completed messages cannot refresh the enclosing phase.

`source_preflight` includes source hello, full held-FD raw/chunk hashing, the complete digest-table reply and the final source stat check. It completes before even target features or a target session is opened. `reconciliation` independently bounds the target's chunk scan. `transfer` bounds the complete chunk sequence, with source and target sharing its absolute deadline. `whole_image_hash` independently bounds final target whole-image readback/hash and commit receipt. These separate explicit budgets can later be qualified for the 11,331,268,096-byte image; this spike does not select appropriate values. No 180-second or 600-second recovery limit is carried over.

Control features output is capped at 4096 bytes, captured with the same nonblocking pipe implementation, and bounded by the explicit control phase/message deadlines. Source and target stderr are drained without threads during waits; each session retains at most 65536 bytes. Child exit/EOF and excess output fail closed. Exit draining is also finite. Host-child cleanup has an explicit separate finite grace; its final kill/wait is finite and reports a failure if the host child cannot be reaped.

## Preserved protections and terminal uncertainty

RSC1 and SOURCE1/SRC1 header bytes, opcodes, payload layouts, chunk size, sequence checks, SKIP behavior, manifest parsing, reconciliation and inverse selection are unchanged. RSC1 `parse`, `status` and `reconcile` are copied exactly and AST-checked against the immutable client. Worker held-FD, canonical path, stat identity, mode/owner/link, sparse rejection, full/chunk hashing and sequential consumption guards are unchanged. Fixed remote/local profile literals and compact chunk tables are verified unchanged.

The parent uses the same verified SOURCE1 process and held descriptor for preflight and live source chunks. Fixed local stock inputs now use a source-only pipe child running the unchanged `worker.serve` and `HeldRaw`; arbitrary profile/path selection was not added. No blocking regular-file read/hash runs in the parent's source-consumption path. An unavailable/mutated/stalled source closes and seals that source session. Source failures during transfer also poison the target session before any further target request.

Every actual pipe read/write checks its absolute deadline immediately before the nonblocking syscall and after it returns, including after readiness and earlier blocking guard work. Malformed frames, timeout, EOF, unverified completion, wrong ACK, bad whole hash and lost commit receipts seal the session with UNKNOWN. A consumed source cannot be reused. The same poisoned target cannot issue status, reconciliation, cleanup, inverse, reconnect or retry requests. Explicit partial trials also seal their session.

Closing/reaping a local host child sends no cleanup opcode and does not prove cancellation of target work. A timeout can occur after the target accepted a chunk or commit. `possible_partition_modification` remains true once a potentially mutating request is attempted. The lost-commit model deliberately records an accepted commit while the host reports UNKNOWN and never records whole-partition success. Any future reconciliation requires the parent's separate decision and fresh session; this implementation does not initiate it.

## Finite offline evidence

`tests/run_qa.py` is the repeatable 60-second supervisor. It starts only this spike's standard-library tests and owned finite Python fake peers. The tests run sequentially, with no worker pool or threads. Each fake peer has a 5-second wall alarm and 5-second CPU limit; the suite has a 35-second CPU limit. Each fake source image is only 2 MiB + 3584 bytes. Ephemeral fake contract/budget/transport fixtures are nonfunctional against real hardware and removed at test teardown; none are supplied as approval artifacts.

`evidence/qa.json` and `qa.log` give the final result, individual case timings, own-process/child CPU and RSS, child count and reaping result. Final result: 46/46 tests passed in 9.273 seconds; all 71 created children were reaped. Aggregate own/child CPU was 3.159 seconds. The measured conservative RSS sum was 265,781,248 bytes (parent peak plus 3 maximum live peers times peak peer RSS), below 1 GiB. Coverage includes partial headers/bodies/ACKs; empty reads and full-pipe writes on both target and source boundaries; near-deadline writability; slow drips; EINTR/EAGAIN and actual short writes; EOF/exit; stderr backpressure and trailing stderr; post-guard expiry; no requests after poison; whole-preflight/reconciliation/whole-image phase expiry; source-before-target gating; source identity/chunk/mutation guards; target binding refusal; UNKNOWN after accepted commit; full multi-chunk writes; SKIP with partition tail preservation; and copied parent adapter success/lost-commit runs. The pinned legacy client still hangs on partial ACK and full-pipe send until its separate fake-child supervisor stops it.

Darwin limits: this host rejected RLIMIT_DATA, RLIMIT_AS and RLIMIT_RSS requests with `ValueError: current limit exceeds maximum limit`; no hard 1 GiB memory cap is claimed. The bounded fixtures and measured conservative sum of parent peak RSS plus observed maximum live peers times peak peer RSS stay below 1 GiB. Darwin provides no enforced one-CPU affinity through this Python harness. Work is sequential and synchronous with no CPU pool; aggregate measured CPU remains below the elapsed single-CPU allowance, but strict CPU isolation is not claimed. CPU rlimits and wall supervision are enforced. A stricter scheduler/memory-containment proof remains external if required; no VM/cloud operation was attempted.

Deadlines bound owned nonblocking pipe I/O; they cannot preempt Darwin filesystem metadata, journal writes/fsync, process creation, or an uninterruptible kernel task. Deadline checks after those guards prevent later protocol I/O with an expired budget; bounded final cleanup reports rather than waits forever. This is not a hardware watchdog, target cancellation mechanism or proof of device throughput. No tablet, builder, ADB, USB, SSH, network, cloud, VM, AOSP/kernel tree, build output or existing image was accessed by the implementation/QA commands.

## Parent continuation

Read this report, `evidence/host-io.patch`, pins, and test evidence; perform fresh independent review. The only supplied run commands are offline:

```sh
python3 -B source/verify_handoff.py
python3 -B tests/run_qa.py
```

The parent retains all future actual metadata/profile admission, full-image qualification, budget selection, authenticated USB binding, external code/contract/source pins, arming and physical commissioning. PLAN_ONLY remains the default. No live commissioning command or usable execute authorization is provided here.
