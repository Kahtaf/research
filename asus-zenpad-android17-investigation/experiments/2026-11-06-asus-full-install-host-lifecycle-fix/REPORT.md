# Host deadline and terminal lifecycle correction

Implemented in a new local spike; fresh independent parent review remains pending. Defaults are PLAN_ONLY. Unknown install SYSTEM/BOOT profiles remain UNBOUND_REFUSED. Hardware budgets remain explicit UNQUALIFIED caller inputs. No physical or flash GO is provided.

The prior implementation, independent review and isolated boolean-fix spike are preserved. `evidence/input-pins.json` and `prepost-pins.json` track all 604 small input files from those spikes. The original RSC1 client remains SHA256 `0072398a0aa2da83bdf176d672e7ec767b6aaf034892fb603054a22549c5bf69`. No target code, header, manifest, image, policy, approval flag, actual source admission, accepted observer/deployer/restorer, build output or original artifact was changed.

## Review packet

`evidence/host-lifecycle.patch` is the exact unified runtime source diff against `2026-11-06-asus-full-install-bounded-host-io/source`. Only six host modules change: bounded_io, bounded_client, parent_remote, source_client, sources and journal. The separate `verification.patch` contains offline verifier changes. `changed-code-pins.json` gives every changed source's old/new hashes. `code-pins.json` pins every Python file, including unchanged original tests and reproduction helpers. `scripts/package_evidence.py` reconstructs these documents and verifies the exact parent boolean delta.

`worker.py`, `pinned.py`, `local_pipe_worker.py`, `original/client.py`, `original/manifest.py`, every fixed profile/chunk export, the three original test files and both original review reproduction files remain byte-exact copies. The verifier checks the unchanged parser/status/reconcile ASTs, fixed profile literals, fixed source command, original client/manifest pins and external rescue client/parent/manifest/common-header pins. The contract's existing hash bindings and fields are retained. Local integrity documents are evidence, not authorization; the parent must externally bind the exact reviewed code, contract, manifest, source and budget hashes before any eventual use.

## Phase completion

Each PipeSession now records whether its current phase actually completed. `complete_phase()` validates the still-active absolute deadline and requires no pending request. `set_phase()` must complete an unfinished outgoing phase before replacing it. Sending, receiving, exact I/O and stream draining reactivate a previously completed phase; completion cannot hide subsequent work.

The writer explicitly completes target control after its final journal flush, reconciliation after its journal flush/fsync, and transfer after the last source-check return. Both source and target validate transfer completion before the target enters the whole-image phase. No BEGIN is sent after expired reconciliation publication; no reconciliation follows expired control publication; no whole-hash request follows an expired final transfer guard.

Source preflight completion is recorded after full held-FD verification and its final check. If the parent requests a SOURCE receipt, the parent checks completion again after that receipt's complete write, flush, fsync and file-context closure, before even opening features. A source whose preflight finished successfully may legitimately idle while target control runs. Similarly, the source's completed control work can idle while target reconciliation runs. Neither legitimate idle interval grants more time to an active operation. Tests exercise both positive cases and expired-active rejection.

No phase names, protocol bytes or source selection change. Source and target still share the exact same Phase object during transfer. Whole preflight, reconciliation and whole-image hashing retain distinct finite absolute caller budgets. Progress never extends a phase or message. No 180/600-second recovery limit or hardware-qualified timing default is introduced.

## Terminal publication and host cleanup

A verified commit response now records `commit_receipt` in memory and `COMMIT_RECEIVED` as an intermediate state. The existing `whole_partition_verified` journal field is retained only in a row explicitly marked `intermediate: true`, alongside `commit_receipt_verified`. It does not establish overall call completion.

The direct writer's source cleanup runs inside its error-to-UNKNOWN handler. Only after source cleanup and a post-cleanup deadline check can its complete writer receipt be written, flushed, fsynced and checked again. A source-close error or delay poisons the target in memory before the error escapes. The actual late target-status reproduction is now refused without an additional target opcode.

The parent invokes the writer with final publication deferred. It owns target exit/draining, its remaining source cleanup callbacks, complete stderr publication/flush/fsync/context closure, and confirmed target child reaping. All these required steps run before final success publication and inside UNKNOWN handling. The final journal is flushed/fsynced, checked, closed and checked again; the session is sealed and checked before successful in-memory completion is assigned. Status/readback/reconciliation use the same parent terminal lifecycle. The API-compatible success value `VERIFIED_COMMIT_RECEIPT` is assigned only after the relevant successful call boundary; the parent never inherits that value early from the writer.

A SUCCESS journal line is a publication candidate until its fsync, post-fsync deadline check and required file-close boundary return successfully. Any later failure poisons in memory first and appends a complete UNKNOWN record while the evidence sink remains usable. If the journal context has already closed, the parent attempts a finite-record append only to the same owned regular evidence inode (O_NOFOLLOW, device/inode/link/cap checks). Close errors and close-time expiry therefore still produce a durable UNKNOWN when that owned file remains usable. A replaced evidence path is never appended. If disk publication itself remains broken, UNKNOWN still governs in memory and the call raises; a visible prior candidate/commit row is not proof that the failed call completed durably. Tests exercise successful UNKNOWN recording after both close failure and close-time expiry, and refusal to touch a replacement inode.

The direct source-client API owns source cleanup and its writer receipt; its caller still owns target descriptors/processes and external evidence-file closure. Callers that need the complete parent lifecycle must defer publication, as the production parent does. No direct-writer completion is used as final parent success.

All short receipt, journal, SOURCE-receipt, stderr and readback-file writes now either finish completely or raise. The shared write helper rejects zero, None, boolean, negative and impossible counts. BoundedJournal keeps its original byte-cap accounting and uses complete sink writes. The adversarial eight-character receipt sink is repaired by finishing the remainder; its resulting JSON receipt is complete. Invalid/no-progress sinks become UNKNOWN.

RemoteSource retains its Popen reference until successful confirmed reaping. The host reaper also retains failed cleanup ownership in `UNREAPED_CHILDREN`, continues closing other streams if one close reports an error, and removes ownership only after confirmed reaping. This registry is an explicit host-cleanup reference, never a reconnect/retry queue. A real owned fake child with injected wait failures proves the reference survives until subsequent explicit host cleanup confirms reaping.

On timeout, lost completion, publication failure or cleanup failure, no further target/source protocol request is permitted on the poisoned session, including status, cleanup, inverse or retry. Filesystem evidence and owned-child closure/reaping are host actions only. They do not cancel, reverse or prove the absence of accepted target work. `possible_partition_modification` stays conservative and commit facts survive poisoning. Lost final commit and accepted-commit/host-failure cases remain UNKNOWN.

## Multi-frame requests and caller types

Readback's op 6 now keeps its pending absolute deadline through both op 0x86 digest and op 0x87 data replies. Only the final frame completes the request. The retained peer's two 0.12-second delays exceed a 0.20-second message budget and are refused without publishing an output; a separate 0.50-second fake-fixture budget succeeds. These are artificial host timings, not device measurements.

The parent applies the exact already-approved one-line `armed is True` correction from the isolated boolean-fix spike. `armed-before.json` fails on the actual original guard; `armed-after.json` passes on the actual new guard. `armed-delta-verification.json` checks the exact patch and its provided before/strict-only-after hashes. This is explicitly a guard-only regression, not a full CLI acceptance claim.

Boundary type checks require policy/phase mappings, finite positive numeric phase/message/cleanup seconds, two-element phase pairs, a contract object, and string mode/hash fields. The exact armed-boolean guard remains intact. No new policy/contract fields, profiles, arbitrary path selection, hash bypass or execute authorization are introduced.

## Actual adversarial evidence

The copied original review harness first ran on the copied original implementation: 29 cases, 15 failed correctness assertions, zero harness errors, all 58 children reaped. These actual reproductions and their observations are retained under `adversarial-before*`.

The byte-exact original harness remains in `review/adversarial.py`. `review/regressions.py` reuses those production flows/injections with corrected post-fix expectations. Expiry cases now require a raised deadline error plus terminal UNKNOWN and exact stopped target opcodes. The short-write case permits the requested complete-write repair and validates all JSON rows. The two final-fsync tests hook actual final publication after confirmed source and target cleanup, instead of relying on the old prematurely assigned success state. Every original review case remains covered; additional cases cover legitimate completed-phase idling, reactivation, positive two-frame readback, cleanup delays, close failures/expiry, identity-bound UNKNOWN append, malformed write counts, SOURCE receipt/stderr completion and retained ownership during failed finite waits.

The first new regression run had one harness failure: its new cleanup-delay hook intercepted feature-child cleanup instead of the target child. It was narrowed to the target, as the independent review itself had done for its cleanup injection. That exploratory run and all its evidence are retained in `regressions-first-run`; it is not acceptance evidence.

`qa.json` / `qa.log` are the unchanged original 46-case suite on the corrected production modules, including legacy partial-ACK/full-pipe hang reproductions. `regression-results.json` / `regressions.log` and per-case `adversarial/` observations are the authoritative additional suite. They exercise the actual copied parent adapter and source writer, not a helper comparison. Target/source fake peers use tiny newly owned files; all original guards, protocol parsing and hash checks remain active except the explicitly mocked fixed reference for that fake source. The adversarial audit hook refuses network and all child executables except the exact owned local fake peers.

## Offline limits and parent continuation

Tests are sequential and finite. The baseline supervisor has a 60-second wall bound and the test process a 35-second CPU rlimit. Regressions have a 55-second wall alarm and 30-second CPU rlimit. Fake peers retain 5-second wall/CPU limits. All fake children must be reaped, all streams closed and every adversarial case's own FD count restored.

Darwin rejected the requested hard memory rlimit. No strict single-CPU affinity or enforced aggregate 1 GiB cap is claimed. Work uses no CPU pool; measured own/child CPU remains below elapsed single-CPU time, and the conservative measured parent-plus-live-peer peak RSS estimate remains below 1 GiB. No VM/cloud containment was attempted. Pipe deadlines cannot preempt Darwin filesystem operations, process creation or uninterruptible kernel cleanup. They detect expiry after those guards return, prohibit subsequent protocol I/O and report finite cleanup failure without forgetting ownership.

Only local public code, compact profiles, owned tiny fake data, pipes and fake children were used. No actual tablet, ADB, USB, root, SSH, network, cloud, VM, build, real source image, full-image copy/rehash, private data or active source/out was accessed. No actual arming/approval file is supplied. Ephemeral fake baseline markers are removed at teardown; adversarial contract/policy/transport markers exist only in memory.

From this new spike, the offline continuation commands are:

```sh
python3 -B source/verify_handoff.py
python3 -B tests/run_qa.py
python3 -B review/regressions.py > evidence/regressions.log 2>&1
```

The parent owns fresh independent review and the external binding of code/contract/source pins, future actual metadata and profile admission, physical budget qualification, authenticated USB selection, arming and all commissioning. This handoff supplies no physical or flash GO.

## Final offline result

46/46 original tests and 45/45 adversarial regressions passed: 91 tests total, all 168 final-suite children reaped. All 29 original review cases are represented in `reproduction-coverage.json`; own FD counts and child stream closure checks pass, and the failed-wait ownership registry is empty.

The original-suite run used 9.145 seconds wall / 3.231 seconds aggregate CPU; conservative peak RSS was 262,045,696 bytes.

The regressions run used 9.064 seconds wall / 4.632 seconds aggregate CPU; conservative peak RSS was 458,014,720 bytes.

The final `evidence/code-pins.json` SHA256 is `3238f27524cfb3ea9a62b668c92105373feb8174d987b4d9328df0c351d80a10`. See `summary.json`, `prepost-pins.json` and `verification.json` for exact evidence. This remains an implementation handoff for fresh independent review.
