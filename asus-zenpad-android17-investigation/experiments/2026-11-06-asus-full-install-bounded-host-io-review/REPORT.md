# Independent review: findings first

The bounded host I/O revision needs parent fixes before acceptance for its stated deadline and terminal-outcome contract. The original protocol and admission protections examined here remain intact. This review authorizes no device work and does not authorize or block the separate accepted stock-rescue tools.

Reviewed subject: `../2026-11-06-asus-full-install-bounded-host-io`. All production source, profile, input evidence, accepted observer/deployer/restorer implementations, and old artifacts were left unchanged. This folder owns only copied small code/profile inputs, tiny newly generated fake data, review code, and evidence. No actual ADB, USB, device, root operation, network, SSH, cloud, VM, private file, key, calibration, source image, AOSP tree, or build output was used.

## 1. P1: replacing the active phase can erase expiry after a blocking guard

Locations: subject `source/bounded_io.py:108-116`; `source/source_client.py:35-40,52-53`; `source/parent_remote.py:63-70`.

`PipeSession.set_phase()` checks the replacement phase after assigning it. It does not establish that the prior active phase completed within its budget. The callers also omit the prior phase check after some blocking journal/guard work. Successful messages and single-use `Budgets.start()` therefore do not prevent these transitions from hiding expiry.

Concrete production-adapter reproduction: `review_parent_reconciliation_fsync_expiry` injects finite latency into the real journal fsync after reconciliation. It waits until the actual reconciliation phase deadline passes, then returns from fsync. The parent returns normally and the fake target records `[1,2,3,4,4,4,5,9]`, including BEGIN, writes, whole hash, and commit. The required outcome is terminal UNKNOWN with no BEGIN after that guard exhausted the phase. [Retained observation](evidence/adversarial/review_parent_reconciliation_fsync_expiry/observation.json).

Other reproductions exercise control journal flush before reconciliation, the final transfer source-check return before whole-image hash, and source-receipt fsync before features/target creation. All cross the old absolute deadline and proceed. The receipt case makes features and target calls after its preflight receipt guard expired. These are injected finite host delays, not measurements of physical hardware or Darwin filesystem stalls.

Smallest parent fix: explicitly check the active phase after each phase's last blocking guard/journal work and before starting its successor. A phase-completion operation should validate the outgoing phase while it is still active. Do not simply reject every old source phase at every later reassignment: a successfully completed source preflight can legitimately be idle while target control/reconciliation runs. Model or record completion at the correct boundary, then share the single transfer phase between source and target as today. The supplementary `review_source_cannot_move_to_new_phase_after_unobserved_expiry` exposes the unguarded API primitive; the production-flow cases above establish the actual caller defects.

## 2. P1: final publication and cleanup errors can leave success as the only recorded outcome

Locations: subject `source/source_client.py:58-65`; `source/parent_remote.py:98-110`.

`write_image()` sets `VERIFIED_COMMIT_RECEIPT` before its `finally: source.close()`. The parent then performs its final fsync and stderr publication/target cleanup. Errors in the parent's final `finally` are outside its UNKNOWN handler. A successful commit receipt is a fact, but it is insufficient to advertise successful completion of a call that subsequently fails.

Production-adapter reproductions:

- `review_parent_stderr_flush_failure_unknown` injects a stderr flush error after commit. The parent raises OSError, but its evidence ends with `whole_partition_verified`; no UNKNOWN follows, and the closed session retains `VERIFIED_COMMIT_RECEIPT`.
- `review_parent_target_cleanup_failure_unknown` lets the actual owned child be closed/reaped, then injects a cleanup reporting error. The parent again raises with only the success line and a success outcome. This injection isolates error routing; it does not claim the real kernel failed to reap.
- `review_parent_final_fsync_expiry` delays the last parent evidence fsync until the whole-image phase expires. No post-fsync deadline check runs; the parent returns normally. The direct API has the same omission after its receipt fsync.
- `review_source_cleanup_failure_direct_api` shows the direct writer raising from source cleanup while its target session remains usable and marked successful. A subsequent actual fake TARGET status request succeeds (`fake idle`), extending the observed opcode list to `[1,2,3,4,4,4,5,9,1]` after the failed call. The CLI catches this particular source-finally exception and downgrades it, but the direct writer does not.

[Stderr publication evidence](evidence/adversarial/review_parent_stderr_flush_failure_unknown/parent-evidence), [cleanup observation](evidence/adversarial/review_parent_target_cleanup_failure_unknown/observation.json), [final-fsync observation](evidence/adversarial/review_parent_final_fsync_expiry/observation.json).

Smallest parent fix: cover all required exit, publication, and host-cleanup steps with the operation's error-to-UNKNOWN handling, preserve `possible_partition_modification`, and check the deadline after final fsync before returning success. Preserve the commit receipt as an intermediate fact; publish overall success only after the relevant call has completed successfully and the final receipt is durable. Closing/reaping a host child must still send no target cleanup opcode and make no target-cancellation claim. If the evidence sink itself is broken, poison in memory first, raise failure, and never interpret a visible earlier verification line as overall success.

Positive controls: a raised final receipt write/fsync error, a failed parent final fsync, a partial target request write, and a lost commit all become UNKNOWN in the tested protected paths. The final receipt fsync failure intentionally retains an intermediate `whole_partition_verified` line followed by UNKNOWN; the last outcome governs.

## 3. P2: the two-frame RSC1 readback reply refreshes one request's message deadline

Locations: subject `source/bounded_io.py:221-235`; `source/parent_remote.py:91`.

`receive()` clears `pending` after the digest reply. The second `receive()` for the same readback request creates a fresh message deadline. Both frames remain under the control phase deadline, but their combined time can exceed the caller's message budget.

`review_parent_readback_two_replies_share_message_budget` uses the actual parent readback branch and an owned finite fake peer. With a 0.20-second message budget and a separate 2-second control phase, the digest arrives at approximately 0.12 seconds and the data frame after 0.24 seconds after request receipt. The parent returns normally and publishes the 19-byte output as successful. [Timestamped peer log](evidence/adversarial/review_parent_readback_two_replies_share_message_budget/target.log), [parent evidence](evidence/adversarial/review_parent_readback_two_replies_share_message_budget/parent-evidence).

Smallest parent fix: retain the request's absolute deadline until all expected reply frames have been received. Make completion explicit for multi-frame replies, or pass that same absolute deadline to the second frame. Preserve opcodes 6, 0x86, 0x87 and existing digest/data validation. No hardware timing value is proposed.

## 4. P2: failed source reaping loses the production ownership reference

Location: subject `source/sources.py:165-174`.

`RemoteSource.close()` assigns `self.process = None` before `reap_owned()` succeeds. If its finite waits fail, later stack cleanup cannot find/reap the child. The bounded wait itself is appropriate; discarding ownership on failure is not.

`review_source_reap_failure_retains_ownership` injects TimeoutExpired at the reap boundary. At failure the fake child is still live and `source.process` is already None. The independent harness retains its own Popen reference and subsequently closes/reaps it; this is why the review has no final child/FD leak. [Observation](evidence/adversarial/review_source_reap_failure_retains_ownership/observation.json).

Smallest parent fix: retain the owned process reference until reaping is confirmed, expose finite cleanup failure without forgetting ownership, and ensure cleanup exceptions enter UNKNOWN handling. Do not add target cleanup, reconnect, or automatic transport retry. The test models the failure; it does not prove or simulate an actual Darwin uninterruptible task.

## 5. P2, inherited: the contract's `armed` field accepts a truthy string

Location: subject `source/parent_remote.py:53`, byte-equivalent validation in the original parent adapter.

`review_parent_contract_armed_type_refused` supplies a correctly hash-pinned in-memory fake contract with `armed: "false"`. The actual parent accepts it, completes the fake write/commit, and returns normally. [Observation](evidence/adversarial/review_parent_contract_armed_type_refused/observation.json).

Smallest parent fix: require `contract['armed'] is True` and validate the caller schema's field types at the boundary. This is an existing adapter defect, not introduced by the bounded I/O diff. An approved external contract hash still protects the exact document; the flaw concerns acceptance of a malformed approved document. No real contract/admission was created by this test. The new policy rejects boolean, zero, negative, NaN, infinite, string, and null seconds before any child is launched; wrong budget/transport/contract pins and a manifest/contract mismatch also stop before a child.

## 6. P2, direct-sink contract: a short successful receipt write is unchecked

Locations: subject `source/source_client.py:58`; unchanged `source/journal.py:17`.

`review_receipt_short_write_unknown` provides a file-backed receipt sink whose final `write()` persists only eight characters and returns 8. The writer flushes/fsyncs that truncated file and reports `VERIFIED_COMMIT_RECEIPT`. The retained journal ends in `{"whole_`; there is no complete durable receipt. [Actual truncated journal](evidence/adversarial/review_receipt_short_write_unknown/journal).

Smallest parent fix: enforce complete journal writes or explicitly require and enforce a sink whose write contract guarantees all characters or an exception. This is a direct API/custom-sink failure model; no naturally occurring short regular-file TextIO write on Darwin is claimed. Raised write/fsync errors are separately tested and do poison the session.

## Preserved protections and successful evidence

The independently reconstructed unified diff exactly matches `host-io.patch`. All 59 tracked subject/original input files are unchanged after review. The review's source/test copies match all 15 supplied code pins; the original external rescue client/parent/manifest/common-header pin checks still pass. Original `client.py` remains SHA256 `0072398a0aa2da83bdf176d672e7ec767b6aaf034892fb603054a22549c5bf69`. The reviewed code-pin document remains SHA256 `f8e480d01c3591ada98343137379cf78d10a4a7075c15d309360f88755784f05`. [Independent integrity result](evidence/integrity.json), [before/after file hashes](evidence/review-input-after.json).

Inspection and fake-peer production flows preserve RSC1 and SRC1/SOURCE1 framing, little-endian fields/opcodes, manifest parsing and original reconciliation/inverse selection. The worker and original parser/status/reconcile ASTs remain unchanged. Explicit inverse success newly records `[1,8,3,4,4,4,5,9]`. Normal transfer, SKIP, whole hash and commit order remain correct. Fixed remote/local profiles, source identity/stat fields, compact chunk tables, canonical path/owner/mode/link guards, sparse rejection, full held-FD preflight, sequential live consumption, and per-chunk digest checks remain. Only newly owned fake image bytes were read/hashed.

The baseline's source-before-features/target checks, bad source/target binding checks, unknown profile/path refusals, and PLAN_ONLY default reproduce successfully. A consumed source cannot be reused. The new reuse case rejects a second write on the same source/target pair before any additional target request. It does not assert that every operation on a successfully completed target session is prohibited; the required prohibition is on poisoned/unknown sessions.

Header, payload, and single-frame reply share one absolute message deadline. The I/O loops check immediately around nonblocking protocol reads/writes, including after readiness. EINTR/EAGAIN, short writes, empty/full pipes, slow drips, malformed ACK/hash, EOF/child exit, stderr backpressure/caps, and finite stream/child draining pass their baseline tests. No successful partial progress extends a message or active phase. The defects above are at phase completion, a multi-frame reply, and final publication/cleanup boundaries.

During transfer SOURCE and TARGET share the same Phase object. Reconciliation and whole-image hash have separate explicit caller budgets. No 180/600-second recovery limit or physical throughput default is introduced. Policy bytes have a separate CLI SHA256 pin, distinct from the unchanged contract/manifest pins. There is no cryptographic link from the old contract to this new policy or new code document; the parent's trusted caller must bind their exact hashes together externally, as the implementation report states. Local verification of self-shipped pins is integrity evidence, not authorization.

Lost completion, a partial request write, source stall during transfer, wrong ACK/hash, and direct raised receipt errors poison the target and preserve possible modification. Added production cases confirm no later TARGET status/reconciliation/inverse/cleanup/retry requests. The fake target can record an accepted commit while the host reports UNKNOWN. Owned child closure/reaping adds no protocol request and establishes no target cancellation. Modification flags remain conservative from attempted mutating requests; they are not evidence that physical blocks changed.

## Reproduction, resources, and limitations

From this folder:

```sh
python3 -B review/verify_integrity.py
python3 -B tests/run_qa.py
python3 -B review/adversarial.py > evidence/adversarial.log 2>&1
```

The baseline completed 46/46 tests in 9.425 seconds, creating/reaping all 71 children. Its own/child CPU was 0.896/2.363 seconds. The conservative RSS sum was 259,981,312 bytes: parent peak 132,628,480 plus three maximum live peers times 42,450,944.

The final adversarial run completed 29 cases in 5.384 seconds: 14 passed, 15 correctness assertions failed, zero harness errors. Those 15 assertions consolidate into the findings above; they are not 15 independent production defects. All 58 children were reaped and all child streams closed. Every case restored its own FD count (4 before/after). Own/child CPU was 0.744/1.957 seconds. The conservative RSS sum was 252,428,288 bytes: parent peak 163,692,544 plus two maximum live peers times 44,367,872. [Final results and tracebacks](evidence/adversarial-results.json), [full log](evidence/adversarial.log). Exit 1 is expected on this unmodified revision; production fixes were deliberately not made here.

Tests run sequentially, with synchronous fake peers and no CPU pool. Parent CPU/wall limits and finite child CPU/wall limits are enforced; no strict one-CPU affinity is claimed. Darwin rejected the attempted hard memory rlimit. The measured conservative RSS estimates are below 1 GiB, but this is not an enforced aggregate memory cap. No VM/cloud containment was attempted. Host filesystem operations and process creation cannot be preempted by these pipe deadlines; after they return, expiry must still be checked correctly.

The new harness uses in-memory fake policy/contract/transport marker inputs, computes their actual pins, and leaves the production pin comparisons in place. It only patches fixed source-reference lookup for the tiny owned fake profile and replaces child creation with exact local Python fake peers. An audit hook refuses network calls and every other child executable. The copied baseline's already-reviewed ephemeral fake contract markers are deleted by its original teardown. No usable execute authorization or profile admission is shipped.

Exploratory earlier logs/case artifacts are retained under `evidence/adversarial-first-run`, `-second-run`, `-third-run`, and `-fourth-run`. The first target-cleanup injection also intercepted feature-child cleanup; it was narrowed to the target before the authoritative final run. These earlier runs are historical, not additional acceptance evidence. The original legacy partial-ACK/full-pipe stall evidence is unchanged, and the actual copied legacy functions again stall until their own finite supervisor stops them.

Continuation: fix the parent implementation in a separate authorized spike, preserve these failing reproductions, re-pin the changed implementation externally, and rerun the baseline and applicable adversarial cases. No live identity, authenticated USB binding, physical timing, whole-OS qualification, source admission, arming, or flash GO is provided. The current physical stock-rescue test uses separate accepted tools; this review does not authorize or block that scope.
