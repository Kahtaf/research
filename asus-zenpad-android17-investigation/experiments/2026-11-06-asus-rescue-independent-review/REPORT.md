# Independent review: stock-kernel RSC1 rescue and block-context variant

**Verdict: accept the narrow context-kind correction and the bounded offline software evidence. Do not declare the rescue flash-ready or the Android 17 installation ready. No physical commissioning, arming approval, or device action is supplied by this review.**

The reviewed image is `../2026-11-06-asus-rescue-block-context-fix/artifacts/candidate-kind-fix/UNTESTED-target-rescue-block-kinds.img`. Its ASUSR002 manifest still has zero records. The parent must resolve the qualification gaps and operational decisions below before mutation. A two-role STOCK-only commissioning route can exercise the existing positive read paths without adding an opcode. It requires a separately reviewed final image and parent-controlled physical session; this report does not create either.

All work is in this new dated spike and its own existing-builder fixture `/srv/android/2026-11-06-asus-rescue-independent-review`. One CPU, 1 GiB address-space limit, sequential compiler invocations; no QEMU was run. No device/ADB/USB/root/flashing operation, calibration/key-content read, cloud lifecycle action, active AOSP source/output mutation, full-size workload rerun, or full SYSTEM/data copy occurred. The recorded r5 build was not polled or altered. Earlier failures and evidence remain intact. No elapsed time establishes the user's presence or physical GO.

## Prioritized findings and exact parent actions

### P1 — Positive physical gates remain untested; zero-record STATUS cannot qualify them

`source/rescue.c:111` returns STATUS before `identity()`, `recovery_ok()`, `open_part()` or `validate_fd()`. A zero-record daemon can report Enforcing and its manifest while CID/GPT/block nodes are unusable. The aggregate fixture explicitly succeeds at STATUS with an invalid CID and missing disk. Prior stock-init QEMU establishes service/proxy behavior, not the tablet's USB authentication or major179 descriptors.

Opcode6 requires a nonzero manifest and validates CID/GPT plus the requested read-only descriptor. It **does not call `recovery_ok()` or accept a recovery pin** (`rescue.c:144–148`). It can read p9, p10 and p25 with a two-role manifest; p26 additionally requires five roles and a compatible policy. The test `test_op6_succeeds_without_p10_pin_after_recovery_changed` passes by design. Readback is not a recovery-pin attestation.

**Small fix:** revise the original report's continuation sequence. Separate pre-arming static/backups review from pre-mutation physical descriptor qualification: demanding positive opcode6 with a zero-record image is impossible. For a later parent-approved STOCK-only two-role image, independently compare actual p10 readback to that final image's padded pin, then run nonmutating reconciliation. Keep STATUS-only, readback-only, reconciliation, and mutation evidence distinct. Do not set any pending approval field merely to get past a builder refusal. The ordered gates below specify a usable sequence without a new write opcode.

### P1 — Production recovery hashing has substantial read amplification

This is in the **shipped production path**, not just a mock. `recovery_ok()` (`rescue.c:70`) opens p10 and hashes all 16,740,352 bytes. Both WRITE and SKIP reach it before their current-chunk read (`:128–135`). A successful image transaction invokes it twice during reconciliation, once at activation, once per chunk, once at whole-image verification, and once at commit: `chunks + 5` complete p10 hashes.

| Transfer | Chunks | p10 bytes from per-chunk checks alone |
| --- | ---: | ---: |
| SYSTEM | 3,580 | 59,930,460,160 |
| DATA | 10,807 | 180,912,984,064 |
| BOOT | 16 | 267,845,632 |
| Total | 14,403 | **241,111,289,856** |

Including the 15 phase hashes across three completed images gives **241,362,395,136 bytes**. This excludes GPT reads, source preflight, reconciliation scans, target current-chunk reads, write/fsync/readback, whole-image reads, SYSTEM/data prerequisite scans and retries. These are derived byte counts, **not measured storage throughput, wear, duration, or power evidence**. The p10 reads use O_DIRECT in production, so a Linux regular-file fixture is especially unsuitable as a speed prediction.

Fresh ARM64 daemon/proxy reproduction matched the delivered binary hashes. Separately, an instrumented `pread` wrapper around unchanged session source counted nine complete 8 KiB recovery reads for four-chunk WRITE and SKIP fixtures: four per-chunk plus five phase reads. The three trace tests passed. No production code was changed.

**Small immediate fix:** add the arithmetic and qualification limit to the handoff; obtain bounded physical latency evidence before planning a long transfer. Keep current checks for initial read-only commissioning. Avoid interpreting repeated SKIP as a cheap flash trial.

**Design recommendation, not a patch or approval:** a phase/connection guard deserves separate review before full-size mutation. Candidate structure: retain full p10 hashes before and after reconciliation, at activation, before whole-image success and commit, and on every fresh connection/reconciliation; hold an independently validated read-only p10 FD for the phase; keep CID/GPT/Enforcing, target held-FD/path/label/geometry/mount/holder checks and a cheap p10 FD/path/label/geometry check on every chunk. Scope cached results to the exact daemon lifetime, manifest, p10 pin, connection and phase, never across reconnects or uncertainty.

That is **not automatically correctness-equivalent**. Holding a block FD and checking inode/stat does not detect changed block contents or silent corruption. Removing per-chunk hashing changes when a changed recovery is detected. A phase approach needs an explicit, justified immutability/exclusive-writer invariant for p10 and an accepted phase-boundary detection model, or an equivalent content-change mechanism. Current process serialization and SELinux rules make that argument plausible but do not prove protection against arbitrary kernel/privileged actors. Do not simply cache `recovery_ok()` or delete it. If that invariant cannot be established without weakening the required check, retain per-chunk hashing and qualify its operational cost. Required regression cases include p10 replacement/mutation at every phase boundary and mid-transfer, changed pin after uncertainty, disconnect/reconnect, stale guard reuse and fd/path replacement.

### P1 for future p26 use — The original pair is not a complete userdata rollback

Roles0/1 restore original SYSTEM/BOOT only. The daemon never writes p10 or the whole disk; it has no p20 role. With five records, the data role is fixed to p26, not a general format operation. SYSTEM is verified before data; install BOOT requires both whole install SYSTEM and whole data. Original BOOT requires original SYSTEM but **does not check or restore stock-compatible data** (`prerequisite`, `:99–105`).

Restoring the original pair after p26 provisioning is therefore not proof that stock Android will boot with the resulting userdata. This is not a two-role commissioning blocker because that phase must leave p26 untouched.

**Small fix:** label the inverse as SYSTEM/BOOT rollback, and require a separate parent-owned stock-compatible data recovery plan before any five-role operation. Preserve factory calibration independently, retain p20 unchanged, and use existing preservation receipts without exposing private bytes. User authorization to destroy internal data does not waive calibration survival. Restoring original recovery remains an external parent operation; the rescue cannot repair its own p10. Keep the verified local SYSTEM/BOOT/recovery bundle available without cloud dependence.

### P2 — Unknown outcome belongs to the host even when daemon STATUS says IDLE

At commit, a successful kernel `frame_out(0x89)` clears `uncertain_image` (`:142–143`). The host can fail to receive that buffered reply. The fresh aggregate test intentionally does not read the commit receipt and subsequently observes `state=IDLE uncertain_image=-1`. This is not unauthorized writing: every subsequent mutation still needs reconciliation and a fresh connection-bound token. It does invalidate any universal claim that every lost final receipt leaves the daemon FROZEN.

**Small fix:** change the comment at `rescue.c:140` and report wording to distinguish send failure from host receipt loss: “A failed final send leaves mutation frozen; a host without a verified commit receipt must treat the outcome as unknown even if a later daemon status is idle.” Keep host behavior unchanged: no automatic resend, no offset resume, fresh explicit reconciliation. Do not infer whole-host success from STATUS or a target-side journal. The journal is tmpfs and is not restart-durable. After daemon death/reboot even the in-memory uncertain selection is gone.

### P2 — Socket timeouts are inactivity limits, not operation deadlines

`SO_RCVTIMEO`/`SO_SNDTIMEO` are 15 seconds in production (`:168`), while `exact_read` loops over progress. The aggregate suite confirms a slowly fragmented frame can take longer than the test socket's two-second timeout and still succeed. Block reads/hashes are outside those socket waits. The proxy has no absolute operation deadline.

**Small fix:** describe idle I/O timeout semantics accurately; do not promise that the writer returns idle within 15 seconds of starting an operation. Parent-side bounded observations must stop with an unknown outcome, never reboot or start a replacement writer merely because a timer expired. Obtain actual later idle proof before explicit reconciliation. No daemon timeout change is required for this review's acceptance.

## Independent acceptance of the concrete image

`evidence/variant-independent.json` comes from a separate Android-v0/MTK/newc parser, not the parent's packager. It checks component lengths/padding, Android SHA1 ID, gzip/newc contents, kernel preservation, header command line, policy, manifest and the compiled-context row multiset.

| Property | Verified result |
| --- | --- |
| Image | 9,541,632 bytes; SHA256 `299e65cbc1b5290b1e9ef89e0495ca5b8eac63d0d6e486d15611624ba63d35ea` |
| Zero-padded p10 digest | `225151bafbb86d0b72abd72299888524b13cb8b651bec7d7b617dc0cbc913f6b` |
| Compiled contexts | `7723428608524a84b06144e4d48836c65219fe48503f230070567063b50b3f89` |
| Unchanged policy | `189c477ac73ecb161a6527f7f98a6fec76a913b0d5cf8d11591d440dc79af842` |
| Change | Only `file_contexts.bin`; all other cpio payloads and metadata unchanged |
| Manifest | ASUSR002, 112 bytes, zero records |
| Ramdisk payload | 2,064,969 compressed bytes |
| Current fit | 2,129,335 bytes before the fixed reservation at `0x44400000`; 7,198,720 image bytes below p10 capacity |

All nine rescue block rules change only from unspecified inode-kind to `-b`; the complete 906-row multiset otherwise matches. The unchanged policy grants no new symlink or block access. A fresh run of the pinned Android7 compiler produced the exact expected contexts. **31 independent lookup cases pass**, covering direct nodes, by-name spellings as block nodes, actual symlink/regular-file modes, and best-match alias selection. **Six independent policy checks pass**, including existing generic block symlink access and denied p10/disk writes/default userdata access.

`ueventd.rc` supplies root:root/0600. In the AOSP Android6 and Android7 ueventd implementations, node creation ORs those permissions with `S_IFBLK`, calls `selabel_lookup_best_match` with the actual mode and alias list, then `mknod` under the chosen creation context. It resets that creation context before `handle_device` creates the separate aliases with `make_link_init`. Thus the block lookup must see the rescue type while a symlink-mode context lookup must fall back to `block_device`. Sources and hashes are saved under `source/` and `evidence/ueventd-source-receipts.json`; see [Android6 devices.cpp](https://github.com/aosp-mirror/platform_system_core/blob/android-6.0.1_r81/init/devices.cpp#L231) and [Android7 devices.cpp](https://github.com/aosp-mirror/platform_system_core/blob/android-7.1.2_r39/init/devices.cpp#L232). The saved init utility's `make_link_init` creates the symlink without explicitly requesting the block-node context.

This is a source/lookup semantics check, **not a proof of exact OEM by-name creation on the tablet**. The image's `/sbin/ueventd` is the unchanged `../init` symlink; saved stock init SHA256 is `e9594c0d1cbe7d05d34acd63e90b424672360ceb09112fa16b5b23390c21b7e5`. Prior actual stock-init QEMU evidence is preserved and relevant but uses virtual hardware. The old unspecified-kind rules demonstrably select rescue block types for symlink-mode lookups; that establishes a class mismatch if those rules label/restorecon a symlink. It does not establish that stock ueventd necessarily mislabeled every link at first creation. The fix removes that ambiguity without widening policy.

The prior review's speculative 2 MiB initrd-clamp concern is superseded by the parent's byte-pinned LK audit: LK replaces the stale DT bootargs. Do not retain “greater than 2 MiB” as a rejection. Current compressed destination starts at `0x44000000`; the fixed reservation begins at `0x44400000`. Any later armed image must have its **actual** compressed extent, all applicable reservations, wrapper/header geometry, kernel/DT preservation and p10 capacity checked anew. Current unarmed fit is not an armed-image pin or proof of runtime boot.

## Contract and source-integration assessment

The real ARM64 daemon and proxy were freshly reproduced byte-for-byte in the isolated fixture: daemon `30ae9252e575d7c9c837783d60e51016a16bcadb46bd38215d8e49e5bb5d1c53`, proxy `f915eca1b2ae5250afef76d3154a853b933278c283f82cfb4eb0cee7d2736d0f`.

- **Endpoint and framing:** RSC1 has a 12-byte header and at most 1 MiB payload. The fixed shell accepts only `-c rescue-v1`, non-TTY I/O, real/effective UID2000, exact shell domain and Enforcing. The daemon requires root/exact rescue domain, the init-owned pathname socket and a lifetime abstract-socket writer lock. Both ends check peer credentials/security domain. The server serializes sessions; it does not claim a hardware-wide exclusive lock against arbitrary privileged code. The secure property settings and prior domain fixtures are consistent; actual secure ADB/USB remains physical work.
- **Targets and identity:** no client paths enter the target protocol. O_NOFOLLOW/O_CLOEXEC/O_DIRECT, held-FD/path inode equality, root:root/0600, SELinux type, major/minor, BLKGETSIZE64, sysfs size/start, exact alias resolution, empty holders and no major179 mount are checked. CID is lowercase32hex hashed without newline; both GPT regions are pinned. These are repeated observations, not atomic kernel exclusion of a separate privileged writer. The production expected original BOOT and GPT pins are compiled in; the reviewed manifest supplies exact original SYSTEM, per-image/chunk and CID pins.
- **Transfers:** reconciliation scans actual bytes; the fresh token is connection-bound. Every WRITE's data must match the compiled manifest chunk; every SKIP re-reads the current target chunk and refuses a mismatch. Nonmatching WRITE needs write/fsync/readback. Sequence/length/short I/O errors stop. Whole-image verification plus explicit commit receipt is needed for host success. A successful committed image closes that connection. No retry, automatic reboot, or offset-only resume exists.
- **Order:** SYSTEM before its BOOT is enforced by full hashes at reconciliation and activation. Five-role data requires install SYSTEM; install BOOT requires SYSTEM and data. A matching reconciliation bit is never permission to skip target verification. Explicit original inverse selection is constrained and does not bypass original SYSTEM-before-BOOT. It cannot be assumed to handle p26 rollback or self-restore p10.
- **Source identity:** the original local client prehashes its selected raw file and checks each later chunk; it reopens the path, so its preflight is not itself a held-FD guarantee. A replacement with wrong bytes still fails the per-chunk hash. The new remote-source adapter strengthens this with one held regular-file FD, fixed profile, metadata/path rechecks and complete preflight before the target shell. Source object/manifest/role/stop count are bound and single-use; every source chunk is checked even when the target sends SKIP. Trusted builder root remains outside the worker's assurance.
- **Remote integration:** reviewed the callback/parent diffs and rechecked **23 source/profile integrity pins**. The parent's **28-test replay** is retained as prior evidence; this review did not repeat its whole implementation or source preflight. The protocol order, target gate calls and unknown-outcome behavior are preserved; no new target opcode exists. The currently shipped adapter binds original SYSTEM/BOOT and pristine data, but **refuses unbound install SYSTEM/BOOT**. It cannot deliver an arbitrary new SDK37 pair by changing role numbers or reusing originals. Actual production full-source preflight remains required in the same transfer session; sample receipts do not substitute for it.

## Evidence ledger and exact qualification limits

| Evidence | Result | Limit |
| --- | --- | --- |
| `evidence/linux-session-tests.json` and `.stderr` | **16/16 pass**, 6.904 s | RESCUE_TEST ordinary files, small geometry; no production block/peer/SELinux proof |
| `scripts/review_sessions.py` | Only prior nonblocking-FD harness mistake corrected | Prior r1 failure and corrected single-case evidence remain in prior spike |
| `evidence/linux-semantics.json`, command log | 31 context cases, 6 policy checks, 2 byte-identical ARM64 builds | Static/compiler proof; no physical label assignment |
| `evidence/recovery-trace.json` | **3/3 pass**, actual unchanged session source behind traced pread | Tiny ordinary-file fixture; not performance evidence |
| `evidence/variant-independent.json` | Concrete new image and nine-row delta pass | Unarmed artifact; no physical boot |
| `evidence/remote-source-integrity.json` | 23 pins pass; original source unchanged | Original adapter's 28 tests relied on parent replay; no source image read here |
| Original `adapter-tests-delivery.txt` | Prior **24/24 pass** retained | Not rerun in full here; eight selected cases are in fresh aggregate |
| Original QEMU block/stock-init results | Prior pass retained; stock-init observer exits42, host timeout124 | Actual stock USB adbd did not enumerate physical hardware; observer substitute; virtual disk geometry |
| Original synthetic fullsize-r4 | Prior 3,580-chunk pass retained | Predates ASUSR002; synthetic SYSTEM, not OEM data; no repeat here |
| Local rollback receipts plus this review's stat check | Three actual files retain expected sizes | Parent's verified hashes accepted from evidence; **not** rehashed here |

No claim is made here about physical eMMC durability, sustained throughput, exact stock OEM ueventd aliases, current device identity, working rescue USB, calibration restoration, Android17 boot, Google certification or hardware function. Broad security certification/CTS is not inserted as an experimental boot gate. Actual SDK37 product provenance, root, Play/Services, debloat and hardware goals remain separate parent acceptance work.

## Ordered commissioning gates — proposal only; parent executes

1. **Explicit physical readiness and fallback.** User presence and any required physical GO must be established, not inferred from 23:03 UTC or elapsed time. Parent selects a viable nearby recovery route and independently available local inverse. Confirm verified factory-calibration preservation by receipt, with no private byte output. No target operation is authorized by this report.
2. **Freeze exact STOCK-only inputs and artifact.** Only original SYSTEM role0/p25 and original BOOT role1/p9; no install pair, p26 role or userdata policy grant. Parent resolves pending review/approval fields deliberately. Use existing verified originals, not a fabricated pair. Package with the accepted `-b` contexts and unchanged narrow policy. Review actual manifest/chunk/whole pins, binary identity, LK reservations and p10 fit. Compute a new final padded p10 pin and bind the actual contract. Never reuse this unarmed image's pin for an armed image.
3. **Parent installs/boots only that reviewed stock-kernel rescue when authorized.** Demonstrate current authenticated shell_v2 non-PTY fixed proxy, correct UID/domain/Enforcing behavior and final manifest identity via STATUS. A status response is endpoint/idle evidence only. Do not claim hardware access from it.
4. **Positive read-only commissioning using existing opcode6.** With a two-role manifest and fresh IDLE connection, read p10 chunks0–15 and stream their aggregate hash; the last chunk is 1,011,712 bytes. Compare all 16,740,352 actual bytes to the exact final padded pin. Read bounded first/middle/last p9 and p25 chunks and compare their bytes/digests to the trusted source tables. Record request part/index, expected length, source comparison, current identity and errors; transport self-hash alone is insufficient. These reads exercise CID/GPT and the actual requested node's read-only FD/mode/label/alias/mount gates. No p20/calibration/raw CID access and no full SYSTEM download. A few samples do not prove whole SYSTEM equality or write durability.
5. **Nonmutating reconciliation.** On a fresh connection, reconcile role0 using the final manifest/p10 pin and inspect all actual target match bits; do not send activation. Stock commissioning expects all SYSTEM chunks to match; a mismatch stops for diagnosis rather than automatically fixing bytes. On another fresh connection, role1 reconciliation also verifies whole original SYSTEM before BOOT. Reconciliation enters a state that rejects opcode6; use separate connections for subsequent readback. Close cleanly and obtain fresh idle proof. Record bounded read and scan timings as observations, not a guarantee for long writes.
6. **Explicit decision before any mutation phase.** Readback/reconciliation do not prove O_RDWR/fsync durability. A stock-matching WRITE or SKIP trial opens writable state but the daemon skips matching bytes, so it also cannot prove a physical write. Do not deliberately corrupt a partition to manufacture write evidence. If parent later approves a bounded stock-only activation/disconnect trial using the existing `stop_after` mechanism, document that limited scope, keep BOOT last, and reconcile before anything else. Resolve read-amplification policy before a full transfer. No new opcode, synthetic armed approval, or automatic continuation is proposed.
7. **Separate full-install gate.** Wait for a validated genuine SDK37 SYSTEM/BOOT pair; finish its source bindings, final packaging, policy and hardware prerequisites. Five-role provisioning additionally needs clean-data and calibration/stock-data-recovery review. On actual mutation, use fresh held-source preflight, idle proof, reconciliation, per-chunk acknowledgement, whole verification and commit; SYSTEM → data (if approved) → BOOT. Lost acknowledgements/receipts stop as unknown. Parent chooses deliberate same-image reconciliation or explicit inverse; no automatic retry/reboot. This review does not certify full flashing readiness.

Concrete handoff: `HANDOFF.json` provides machine-readable results and priorities. The original implementation and parent integration files were not edited. The next useful parent action is to adopt the narrow static verdict and documentation corrections, decide the p10 guard strategy without weakening it, and retain the physical gate as pending.
