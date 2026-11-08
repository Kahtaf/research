# Independent review: one remaining finding

The six prior findings no longer reproduce in their supplied repaired production flows. All 91 supplied cases pass. Independent fault probes found one narrower P2 gap in persistent UNKNOWN framing after partial publication. The in-memory safety state remains correct in these reproductions: UNKNOWN, possible modification retained, source consumed, no further protocol commands. This is a review finding, not deployment approval.

Reviewed subject: `../2026-11-06-asus-full-install-host-lifecycle-fix`. Production, prior implementation/review artifacts, and the accepted stock-rescue tools were not edited. This spike contains byte-exact compact review copies and new review-only tests/evidence.

## P2: a recoverable partial record write can swallow the terminal UNKNOWN record

Locations in the subject and unchanged local copies: `source/source_client.py:29-35` and `:37-42`, `source/journal.py:5-13`, and the closed-file recovery path `source/parent_remote.py:31-45`.

`write_all()` correctly completes positive short writes and rejects a failed/no-progress continuation. It cannot make a write atomic. If a sink persists part of a JSON row and then raises, `record_unknown()` appends its JSON immediately after that prefix. Neither the normal append nor the identity-bound reopened-file append establishes a fresh record boundary. The subsequent append can return successfully and be flushed/fsynced while the terminal line is still malformed JSON. The sink in both reproductions recovers: the failure is one-shot, and the remaining writes, final flush, fsync and file closure succeed.

Two actual production-path reproductions fail the desired complete-terminal-record assertion:

- `review_direct_partial_success_then_write_error_records_unknown`: the real direct writer receives and verifies commit, closes/reaps its source, then starts its final SUCCESS publication. An owned file-backed sink persists 24 characters, raises OSError on the continuation, and accepts all subsequent writes. The writer raises and poisons correctly. Its durable final line is `{"outcome": "SUCCESS", "{"outcome": "UNKNOWN", "possible_partition_modification": true, "automatic_retry": false}`. There is no independently parseable UNKNOWN row. [Actual journal](evidence/adversarial/review_direct_partial_success_then_write_error_records_unknown/journal), [observation](evidence/adversarial/review_direct_partial_success_then_write_error_records_unknown/observation.json).
- `review_cli_partial_unknown_then_recovered_sink_records_unknown`: the real parent CLI write flow reaches intermediate commit, then its required stderr flush raises. Its first UNKNOWN write persists 24 characters and its continuation raises once. After the evidence context closes, the parent's real inode-bound recovery append successfully flushes/fsyncs another UNKNOWN payload onto the unfinished first payload. The final line is `{"outcome": "UNKNOWN", "{"outcome": "UNKNOWN", "possible_partition_modification": true, "automatic_retry": false}`. There is again no parseable terminal UNKNOWN record. [Actual parent evidence](evidence/adversarial/review_cli_partial_unknown_then_recovered_sink_records_unknown/parent-evidence), [observation](evidence/adversarial/review_cli_partial_unknown_then_recovered_sink_records_unknown/observation.json).

Both fake targets record exactly `[1,2,3,4,4,4,5,9]` and accepted commit. Both sessions retain the commit digest, `possible_partition_modification=True`, and `outcome=UNKNOWN`; both sources remain consumed and unavailable. Actual subsequent send/receive/phase-restart attempts are refused. Direct target ownership remains with its caller; the parent CLI session is closed. All owned children are reaped. These facts bound the finding to durable evidence framing; this does not demonstrate a false successful return or a request after poison.

The injection uses ordinary owned test files behind short-write/failure wrappers. It does not claim an observed naturally occurring Darwin TextIO short write or disk failure. It exercises the direct custom-sink contract explicitly supported by this revision, and the actual CLI failure/reopen path under a recoverable publication fault.

Smallest fix direction: give UNKNOWN recovery a known record boundary before its JSON, including the closed-file append path. A framing separator before the terminal record can preserve the torn bytes for diagnosis while making the new last record independently parseable; include that separator in journal-cap accounting and define torn-row handling. An alternative for an exclusively owned seekable journal is to restore its last confirmed record boundary before publishing UNKNOWN. Preserve inode/no-follow/link/cap checks, poison before any sink work, raise the original operation failure, and send no protocol request. Do not infer successful durable UNKNOWN publication solely from completion of its payload when its starting boundary is unknown. No fix was applied here.

Affected exact SHA256 pins:

- `source/source_client.py`: `a620a009ecbb724b4a4c2be9313b191b5d1912ea1c353185fc4896fd0fe84927`
- `source/parent_remote.py`: `e98bddea37d52e864b02c7015c5649d88b009623af532ede52c3ee71ce0fd023`
- `source/journal.py`: `9154ff8b461f1e1c5be0c7ac1705fcbc06beefbff394ae1e0d7d3e1dfbf8b683`
- Subject `evidence/code-pins.json`: `3238f27524cfb3ea9a62b668c92105373feb8174d987b4d9328df0c351d80a10`
- Subject `evidence/host-lifecycle.patch`: `389a4bca69e3d4b82c4f5d20828bf75a4d373ef1a269139563198416ba48ce5d`

## Disposition of all six prior findings

1. Outgoing phase completion is repaired in the examined production paths. Control journal delay stops at `[1]`; reconciliation fsync delay stops before BEGIN; final transfer-source-check delay stops before whole hash. Preflight receipt expiry opens neither features nor target. Completed preflight may idle through control, and completed source control may idle through target reconciliation. New I/O reactivates completion checks. The added pending-request boundary test poisons rather than completing or restarting an unresolved request.

2. Final publication and cleanup exceptions now produce terminal UNKNOWN in memory with modification uncertainty. Supplied cases cover direct/parent final fsync failure/expiry, source close, target cleanup reporting, stderr flush/context close, evidence context close/expiry, source cleanup delay and target cleanup delay. The final publication hook actually runs after source disposal and confirmed target reaping. The added deferred-writer test observes `COMMIT_RECEIVED`, consumed source and no source process before injecting a parent failure; no SUCCESS row appears. Added status, reconciliation and readback CLI stderr failures also become UNKNOWN with modification false. Added write/flush/fsync failures while publishing UNKNOWN and combined lost completion/cleanup-report/failure-sink errors retain poison and reject later commands. The framing finding above is the remaining persistent-evidence qualification.

3. Both readback replies share one absolute request deadline. The actual parent op 6 flow with two 0.12-second delays fails under a 0.20-second message allowance, before output creation; the 0.50-second positive case succeeds. Opcodes 6/0x86/0x87 and digest/data verification remain unchanged. These are fake timing fixtures, not physical timing measurements.

4. Source ownership survives failed reaping. The actual RemoteSource reference and `UNREAPED_CHILDREN` registry retain the real owned fake Popen during injected wait failures; explicit later host cleanup reaps it and removes the registry entry. The added source-stream-close reporting error still closes the other streams and confirms reap, poisons the writer, and leaves the source reference reachable until its next explicit close. Host terminate/kill/reap actions send no target opcode and make no cancellation claim.

5. The exact isolated parent armed-boolean correction is incorporated. Independent reconstruction matches the original strict-only patch and pins: before `20896740a02181fd78142038e12a9a4a64bdac42ccef9cc46036a917ea71deda`, strict-only after `b8c807e557dafffdea6e45acda6220e6bd81ca0f81c34b515f5ad3da98723ad9`. The repaired guard AST is identical to that strict-only guard. In addition to guard extraction, the full fake CLI refuses False, strings, integers, null, lists and objects before any child; literal True reaches the positive fake flow. Boundary policy/schema and all supplied wrong-pin refusals pass.

6. Positive short receipt writes now complete; no-progress and invalid counts become UNKNOWN. Original eight-character writes produce complete JSON on the repaired writer. Journal, SOURCE receipt, stderr, and added two-byte readback-output short-write cases complete as required. Zero/None/boolean/negative/impossible counts fail closed. A partial write followed by a raised continuation error is the additional framing boundary identified above; it does not restore the old successful short-receipt outcome.

Every one of the prior review's 29 named production cases is present in the actual successful 45-case regression observations; independent AST/name verification records the mapping in [integrity.json](evidence/integrity.json). Adapted expectations are appropriate: fixed expiry cases now raise, completed short writes are accepted, and final parent fsync injections hook real final publication instead of the obsolete premature success state. The untouched prior adversarial harness remains beside the adapter for inspection; running its obsolete expectations is not counted as fixed-code acceptance.

## Preserved behavior and integrity

Independent reconstruction exactly matches both supplied source diffs and every changed-code hash. All 20 subject Python pins, 19 packet pins, 604 prior input pins and 1,086 before/after tracked files verify. Local source, profile, original test and supplied reproduction copies remain byte-exact. [Integrity result](evidence/integrity.json), [before pins](evidence/inputs-before.json), [after pins](evidence/inputs-after.json), [review code pins](evidence/review-code-pins.json).

`worker.py`, fixed remote/local profile literals and chunk exports, `pinned.py`, local worker, original client and manifest remain unchanged. The independent parser/status/reconciliation/inverse AST comparison passes. Original client remains SHA256 `0072398a0aa2da83bdf176d672e7ec767b6aaf034892fb603054a22549c5bf69`. The four referenced external rescue source pins are also checked without editing or expanding review implementation scope to those accepted artifacts.

Inspection and actual fake flows preserve RSC1/SRC1/SOURCE1 framing, little-endian fields, manifest parsing, reconciliation, explicit inverse, sequential chunk SHA checks, SKIP selection, partition tail preservation, whole hash and commit order. Positive inverse remains `[1,8,3,4,4,4,5,9]`; normal and SKIP flows pass. Held-FD/path/identity/stat, full preflight and sparse rejection remain active against newly owned fake bytes. Source verification and optional source-receipt work precede features/target creation. No real image was read or rehashed.

Added consumption coverage proves a successful source cannot be moved to a fresh target/budget instance: the second write is refused before any additional target request, the new target becomes UNKNOWN without modification, and the first call's success is not rewritten. This does not invent a prohibition on every operation after successful direct completion; poisoned sessions remain the prohibited boundary.

PLAN_ONLY is unchanged. Unknown install SYSTEM/BOOT profiles remain UNBOUND_REFUSED. Budget values remain explicit UNQUALIFIED caller inputs with separate policy pins. Integrity of shipped pins is not authorization or a cryptographic binding from the old contract to new code/policy: the parent must bind the reviewed hashes externally before any eventual use.

## Reproduction and limits

From this review spike, run sequentially:

```sh
python3 -B scripts/verify_review.py
python3 -B tests/run_qa.py
python3 -B review/regressions.py > evidence/regressions.log 2>&1
python3 -B review/focused.py > evidence/focused.log 2>&1
```

The first three commands pass; the last intentionally exits 1 for the two assertions forming the single finding. The copied `source/verify_handoff.py` expects its implementation packet; use this review's independent verifier here. The supplied verifier was also run read-only in the original subject, with output retained in `evidence/supplied-verification.json`.

The final baseline is 46/46 passing, 71 children; supplied regressions are 45/45 passing, 97 children; focused tests are 12/14 passing with two correctness assertion failures and no harness errors, 36 children. Final total: 105 tests, 103 passing, all 204 children reaped. Focused and regression observations confirm each case restores its own FD count and child streams are closed; the failed-reap registry ends empty. [Baseline](evidence/qa.json), [regressions](evidence/regression-results.json), [focused results and tracebacks](evidence/focused-results.json), [full focused log](evidence/focused.log).

Measured final test-process wall / aggregate own-and-child CPU / conservative peak RSS estimate:

- Baseline: 9.663 s / 3.542625 s / 248,283,136 bytes.
- Regressions: 9.182515 s / 4.676934 s / 407,781,376 bytes.
- Focused: 2.544744 s / 1.731490 s / 276,660,224 bytes.

RSS estimates sum parent peak and maximum live peer count times the largest child peak; raw rusage values and the calculation are retained in `evidence/summary.json`. They describe this tiny offline workload only. Tests execute sequentially, with synchronous owned peers, no CPU pool, finite parent CPU limits (35/30/30 seconds), finite peer CPU/wall limits (5 seconds), and parent wall supervision (60/55/55 seconds). The independent verifier has 15-second CPU and 30-second wall bounds.

Darwin rejected the attempted hard memory rlimit. Strict single-CPU affinity and an enforced aggregate 1 GiB cap are not claimed. The measured estimates are below 1 GiB; no VM/cloud containment was used. Host filesystem calls, process creation, and uninterruptible kernel cleanup cannot be preempted by pipe deadlines; the reviewed checks must detect expiry after those calls return. No hardware budget is measured or qualified.

An initial focused run is retained in `evidence/focused-first-run`. One cleanup hook also caught the feature child and was narrowed to the target before the authoritative run. Its original lost-commit/partial-UNKNOWN scenario happened to get an extra valid UNKNOWN from redundant parent handling, so the final probe instead injects the partial UNKNOWN at the actual parent cleanup boundary. Those preliminary results are not acceptance evidence; their 35 owned children were also reaped.

All work was public, local and offline. Only tiny owned fake files, pipes and finite fake children were used. No actual ADB executable, device, root, USB, network, SSH, cloud, VM, build, real source image, private material or real approval file was accessed or created. Fake schema markers are in memory in the adversarial/focused flows; ephemeral baseline fixtures are removed by teardown. No R9 parent process/status/source/out inspection occurred. The tablet's user-reported stock-only diagnostic recovery awaiting parent manual commissioning was not touched. Prior accepted observer/deployer/target/rescue artifacts remain outside review implementation scope.

Continuation: address the one framing gap in a separately authorized implementation spike, retain these failing reproductions, re-pin the implementation, and rerun the supplied and focused suites. This review supplies no production edits, deployment approval, runtime/flash GO, or physical commissioning authority.
