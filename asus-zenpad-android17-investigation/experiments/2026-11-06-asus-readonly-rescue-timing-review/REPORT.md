# Independent host-only timing review

Decision: ready for parent decision within the stated standalone CLI scope. No blocking software defect found. One low-severity ownership-contract issue affects in-process use; no physical GO or execution authority is conferred.

Reviewed `source/measure.py` SHA256 `9a28b375223c1833fbb017f814dd82b592dd6fd649f9257a35e3ce046078a0b9`, `source/test_measure.py` SHA256 `a7ba1ced2146b700d9d67fc95759765d2b73ec2ff25c12bcaf5256a535786597`, README and implementation receipt. The byte-identical snapshots are in `snapshot/`. Required target semantics were read in production rescue.c/common.h, build HANDOFF and independent REPORT section “Existing opcode 2 as future timing input.” Exact hashes for all 10 inputs are in `evidence/unchanged-input-receipt.json`.

## Finding: low severity, invalid arguments do not consume the function's owned stream

Location: reviewed `source/measure.py:39–44`, before its `try/finally` at lines 62–90.

Reproduction: create an actual `socket.socketpair()`, call `measure(host, float('nan'))`, catch ValueError. `host.fileno()` remains valid and peer.recv times out rather than seeing EOF. The same applies to zero/negative/infinite/excessive deadlines. No request is sent. `test_reproduce_invalid_deadline_does_not_consume_owned_stream` records this behavior.

This contradicts the function's unconditional “Consume a fresh owned socket” contract. A long-lived Python caller that catches rejection retains the transport. Main also leaves inherited ownership unacquired during input pin, evidence-open and initial fsync failures; `test_reproduce_preflight_failure_leaves_fd_open_in_process` and the initial-fsync test demonstrate that boundary. In the delivered standalone CLI, uncaught failure terminates the process and the OS closes its inherited descriptors. The CLI prevalidates deadlines, so the function issue is not reachable from a valid CLI execution. This is not an activation, partition-write, retry or supported-CLI transport leak.

Smallest fix for `measure`: put validation and start/deadline initialization under the same outer try/finally that closes the stream, and assert EOF/closed in invalid-deadline tests. For any supported in-process `main()` embedding, acquire validated socket ownership before preflight within an encompassing finally, or explicitly document subprocess-only use and caller ownership on preflight rejection. Do not blindly close arbitrary unvalidated FDs. Originals were not edited.

## Verified behavior

- The 80-byte request is exactly RSC1/opcode2/length68, manifest `605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47`, full current p10 `3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a`, index1. No selector, discovery, ADB, activation or second protocol request exists in this implementation.
- The public fixed manifest was independently parsed: exactly two roles, SYSTEM p25 then BOOT p9, BOOT count16. Exact-consumption result and public layout are in `evidence/manifest-public-layout.json`. Source volume SYSTEM + BOOT + 2*p10 equals 3,804,123,136 bytes, excluding identity/GPT and protocol overhead. This is arithmetic, not measured device throughput.
- Exact header (RSC1, 0x82, length48) and all sixteen bitmap bytes equal to 1 are required. Token is never logged or printed. All 48 single-position/nonbinary bitmap cases and all 60 incomplete reply prefixes reject. Original nine malformed/error/nonmatching cases pass.
- Actual AF_UNIX stream tests cover fragmented success, slow byte fragments exceeding the whole deadline, send backpressure, EOF after completion, CLI success/rejection, and no second request. A single monotonic deadline is reapplied across reads; real sendall timeout is bounded. Selected injected settimeout/sendall/recv exceptions also close. This bounds host observation; it cannot cancel a target read.
- The CLI rejects connected AF_UNIX datagram and unconnected stream descriptors. Authentication/freshness remains the trusted parent's responsibility; no independent target authentication is claimed.
- PLAN_ONLY produces a plan and opens no transport. Existing evidence is not overwritten. A fresh 0600 JSONL evidence file is file-fsynced, then its directory is fsynced before socket construction or request. Initial fsync failure sends nothing. A completion row is flushed/fsynced before success stdout. Actual success and rejection records were read back after subprocess termination.

## Evidence interpretation and limitations

An injected failure of the completion fsync produces three rows: UNKNOWN, OBSERVED_MATCH, UNKNOWN, then raises and emits no success stdout. The error path fsyncs the terminal UNKNOWN if storage permits. The intermediate success row can therefore exist even after a failed completion; presence of any OBSERVED_MATCH row alone is not completion evidence. Parent should require successful CLI return and matching success stdout plus terminal OBSERVED_MATCH. A small README clarification of this acceptance rule is recommended. If final/error fsync both fail or the process dies mid-record, no durable completion can be inferred; retain UNKNOWN. This is not a claim of power-loss testing or independently authenticated measurement evidence.

The timer starts immediately before sendall and ends after reply validation; it excludes input hashing, evidence setup and result fsync. Source pins are locally checked, not a measurement of the running target's bytes. The caller must bind this observation to its separately commissioned exact trusted parent image/kernel and run identity. The documented connection-local recovery_pin/token/state changes and possible stale RAM journal.new removal agree with production semantics; no partition write occurs in opcode2. A single observation is not whole-restore timing qualification.

Local evidence: six unchanged implementation test methods plus thirteen independent methods, 19 total, pass on Python 3.13.14. `scripts/review_tests.py` imports the byte-identical owned snapshot and redirects only its BUILD reference to the original fixed public files for pin checks; no production file changes. Tests use local sockets, temporary evidence inside this review spike, and mocked fsync exceptions. No device, transport discovery, VM, root, SSH, cloud, private payload, credential or other worker operation occurred.

Harness corrections are retained transparently: two initial token-fixture length assertion failures, then a datagram-close assumption corrected to allow macOS ConnectionResetError as well as timeout. These failures occurred in owned review code and do not indicate production defects. Final run is `evidence/tests.log`.
